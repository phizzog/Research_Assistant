# Instructions for Implementing Tavily Search with Supabase and Gemini LLM

Here's a step-by-step guide to implement a system that analyzes existing source summaries in your Supabase database, identifies knowledge gaps, and uses Tavily search to find additional relevant sources.

## 1. Set Up Dependencies

```javascript
// Install necessary packages
npm install @supabase/supabase-js @google/generative-ai tavily-ai
```

## 2. Initialize Clients

```javascript
// Initialize clients
import { createClient } from '@supabase/supabase-js';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { TavilySearchAPIClient } from 'tavily-ai';

// Set up environment variables
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;
const geminiApiKey = process.env.GEMINI_API_KEY;
const tavilyApiKey = process.env.TAVILY_API_KEY;

// Initialize clients
const supabase = createClient(supabaseUrl, supabaseKey);
const genAI = new GoogleGenerativeAI(geminiApiKey);
const tavily = new TavilySearchAPIClient(tavilyApiKey);
```

## 3. Fetch Project Data from Supabase

```javascript
async function fetchProjectData(projectId) {
  // Fetch project details
  const { data: project, error: projectError } = await supabase
    .from('projects')
    .select('title, goals')
    .eq('id', projectId)
    .single();
    
  if (projectError) throw projectError;
  
  // Fetch project sources
  const { data: sources, error: sourcesError } = await supabase
    .from('sources')
    .select('*')
    .eq('project_id', projectId);
    
  if (sourcesError) throw sourcesError;
  
  return { project, sources };
}
```

## 4. Create Gemini Prompt to Identify Gaps

```javascript
function createGeminiPrompt(project, sources) {
  return `
  # Project Analysis Task
  
  ## Project Information
  Title: ${project.title}
  Goals: ${project.goals}
  
  ## Current Sources and Summaries
  ${sources.map(source => `
  Source: ${source.name}
  Summary: ${source.summary}
  `).join('\n')}
  
  ## Your Task
  1. Analyze the project title, goals, and existing source summaries.
  2. Identify 3-5 specific knowledge gaps or areas where the current sources lack sufficient information to fully support the project goals.
  3. For each gap:
     - Provide a clear description of the missing information
     - Suggest 2-3 specific search queries that would help find sources to fill this gap
     - Rate the importance of filling this gap on a scale of 1-10
  
  ## Output Format
  Return a JSON object with this structure:
  {
    "identified_gaps": [
      {
        "gap_description": "Description of the knowledge gap",
        "importance": 8,
        "suggested_queries": ["query 1", "query 2", "query 3"]
      }
    ]
  }
  `;
}
```

## 5. Process with Gemini LLM

```javascript
async function identifyGapsWithGemini(prompt) {
  const model = genAI.getGenerativeModel({ model: "gemini-1.5-pro" });
  
  try {
    const result = await model.generateContent(prompt);
    const response = result.response;
    const text = response.text();
    
    // Parse JSON from the response
    // The response might contain markdown formatting, so we need to extract just the JSON part
    const jsonMatch = text.match(/```json\n([\s\S]*?)\n```/) || 
                      text.match(/```\n([\s\S]*?)\n```/) || 
                      text.match(/{[\s\S]*}/);
                      
    if (jsonMatch) {
      return JSON.parse(jsonMatch[1] || jsonMatch[0]);
    } else {
      throw new Error("Failed to parse JSON from Gemini response");
    }
  } catch (error) {
    console.error("Error with Gemini API:", error);
    throw error;
  }
}
```

## 6. Perform Tavily Searches Based on Gemini Output

```javascript
async function performTavilySearches(gaps) {
  const searchResults = [];
  
  // Sort gaps by importance (highest first)
  const sortedGaps = [...gaps.identified_gaps].sort((a, b) => b.importance - a.importance);
  
  // Take the top 3 gaps
  const topGaps = sortedGaps.slice(0, 3);
  
  for (const gap of topGaps) {
    // Take the first 2 queries for each gap
    const queries = gap.suggested_queries.slice(0, 2);
    
    for (const query of queries) {
      // Perform search
      try {
        const searchResponse = await tavily.search({
          query: query,
          search_depth: "advanced",
          include_domains: [], // Optional: include specific domains
          exclude_domains: [], // Optional: exclude specific domains
          max_results: 5
        });
        
        searchResults.push({
          gap_description: gap.gap_description,
          query: query,
          results: searchResponse.results
        });
      } catch (error) {
        console.error(`Error searching for query "${query}":`, error);
      }
    }
  }
  
  return searchResults;
}
```

## 7. Process and Store Search Results

```javascript
async function processAndStoreResults(projectId, searchResults) {
  // Extract and process the search results
  const processedSources = [];
  
  for (const searchResult of searchResults) {
    for (const result of searchResult.results) {
      // Generate a source_id
      const source_id = `source_${result.url.replace(/[^a-zA-Z0-9]/g, '')}_${Date.now()}`;
      const document_id = `tavily_${Date.now()}`;
      
      // Process the result into your source format
      processedSources.push({
        name: result.title,
        title: result.title,
        summary: result.content, // You might want to have Gemini generate a concise summary
        added_at: new Date().toISOString(),
        source_id: source_id,
        document_id: document_id,
        ai_generated: true,
        display_name: result.title,
        project_id: projectId,
        url: result.url,
        gap_filled: searchResult.gap_description
      });
    }
  }
  
  // Use Gemini to generate summaries for each result
  for (const source of processedSources) {
    const summaryPrompt = `
      Generate a concise summary (max 200 words) of the following content that captures the key points:
      
      Title: ${source.title}
      Content: ${source.summary}
      
      Summary:
    `;
    
    try {
      const model = genAI.getGenerativeModel({ model: "gemini-1.5-pro" });
      const result = await model.generateContent(summaryPrompt);
      source.summary = result.response.text().trim();
    } catch (error) {
      console.error("Error generating summary:", error);
      // Keep the original content as summary if summary generation fails
    }
  }
  
  // Store in Supabase
  const { data, error } = await supabase
    .from('sources')
    .insert(processedSources);
    
  if (error) {
    console.error("Error storing sources:", error);
    throw error;
  }
  
  return processedSources;
}
```

## 8. Main Function to Tie Everything Together

```javascript
async function analyzeAndExtendSources(projectId) {
  try {
    // Step 1: Fetch project data
    const { project, sources } = await fetchProjectData(projectId);
    
    // Step 2: Create prompt for Gemini
    const prompt = createGeminiPrompt(project, sources);
    
    // Step 3: Identify gaps with Gemini
    const gaps = await identifyGapsWithGemini(prompt);
    
    // Step 4: Perform Tavily searches
    const searchResults = await performTavilySearches(gaps);
    
    // Step 5: Process and store results
    const newSources = await processAndStoreResults(projectId, searchResults);
    
    return {
      identified_gaps: gaps.identified_gaps,
      new_sources_count: newSources.length,
      new_sources: newSources
    };
  } catch (error) {
    console.error("Error in analyzeAndExtendSources:", error);
    throw error;
  }
}

// Example usage
analyzeAndExtendSources('project-123')
  .then(result => console.log("Analysis complete:", result))
  .catch(error => console.error("Analysis failed:", error));
```

## 9. Additional Considerations

1. **Rate Limiting**: Implement rate limiting for API calls to Gemini and Tavily
2. **Error Handling**: Add more robust error handling and retries for API calls
3. **Deduplication**: Check if found sources are already in your database before adding them
4. **User Feedback**: Add a mechanism for users to review and approve sources before they're added
5. **Periodic Runs**: Set up a scheduled job to run this analysis periodically
6. **Logging**: Implement detailed logging for debugging

This implementation gives you a complete system that:
- Fetches your current project info and source summaries
- Analyzes them with Gemini to identify knowledge gaps
- Generates specific search queries for those gaps
- Uses Tavily to search for relevant sources
- Processes and stores the results back in your Supabase database