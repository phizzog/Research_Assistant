// components/ResearchQuestionsForm.tsx
'use client';

import { useState } from 'react';

interface Question {
  prompt: string;
  options: { label: string; text: string }[];
}

interface Response {
  question: string;
  answer: string;
}

interface ResearchQuestionsFormProps {
  onComplete: (responses: Response[]) => void;
  projectName?: string;
}

const questions: Question[] = [ /* Paste the questions array from Step 2 here */ 
    {
        prompt: "Before selecting a research approach, it's helpful to know the differences. Based on your initial thoughts, which type of data do you anticipate working with the most?",
        options: [
          { label: "A", text: "Numbers, measurements, and statistics (Quantitative Research)" },
          { label: "B", text: "Words, themes, and personal experiences (Qualitative Research)" },
          { label: "C", text: "A combination of both numbers and words (Mixed Methods)" },
        ],
      },
      {
        prompt: "Research worldviews shape the way we approach studies. Which of these statements best describes how you view knowledge?",
        options: [
          { label: "A", text: "I believe reality can be measured objectively with data. (Postpositivist)" },
          { label: "B", text: "I believe knowledge is constructed through individual experiences. (Constructivist)" },
          { label: "C", text: "I want my research to drive social change. (Transformative)" },
          { label: "D", text: "I think the best approach depends on the research problem at hand. (Pragmatist)" },
        ],
      },
      {
        prompt: "Your research design should align with your research goals. Let's determine the best fit for your study. Based on your research topic, which of these best describes your approach?",
        options: [
          { label: "A", text: "I want to test a hypothesis and analyze numerical data. (Quantitative Design)" },
          { label: "B", text: "I want to explore people's experiences through interviews. (Qualitative Design)" },
          { label: "C", text: "I want to combine surveys with interviews for a deeper analysis. (Mixed Methods Design)" },
        ],
      },
      {
        prompt: "Different research questions require different methods. Let's explore your options. Which best describes your data collection approach?",
        options: [
          { label: "A", text: "Surveys and structured experiments. (Quantitative Methods)" },
          { label: "B", text: "Interviews, observations, and narratives. (Qualitative Methods)" },
          { label: "C", text: "A combination of both. (Mixed Methods)" },
        ],
      },
      {
        prompt: "Which data collection method fits your research?",
        options: [
          { label: "A", text: "I will conduct an experiment with controlled variables. (Quantitative – Experimental Research)" },
          { label: "B", text: "I will interview participants to understand their perspectives. (Qualitative – Interviews)" },
          { label: "C", text: "I will combine survey data with in-depth case studies. (Mixed Methods – Integrative Approach)" },
        ],
      },
      {
        prompt: "Analyzing data correctly is crucial for accurate findings. Let's identify the best approach for your study. How do you plan to analyze your data?",
        options: [
          { label: "A", text: "Using statistical tests like regression and t-tests. (Quantitative Analysis)" },
          { label: "B", text: "Identifying themes and coding responses. (Qualitative Analysis)" },
          { label: "C", text: "Integrating statistics with thematic analysis. (Mixed Methods Analysis)" },
        ],
      },
      {
        prompt: "Your philosophical worldview shapes how you think about research. Let's check your alignment:",
        options: [
          { label: "A", text: "I believe in objective truth and measurable data. (Postpositivist)" },
          { label: "B", text: "I believe knowledge is socially constructed. (Constructivist)" },
          { label: "C", text: "My research aims to challenge social inequalities. (Transformative)" },
          { label: "D", text: "I want to use whatever method best solves my research question. (Pragmatist)" },
        ],
      },
      {
        prompt: "Research is not one-size-fits-all. Before choosing a method, consider these factors. Which is most important for your study?",
        options: [
          { label: "A", text: "I need to test a hypothesis and measure numerical outcomes. (Best for Quantitative)" },
          { label: "B", text: "I need to explore ideas and understand perspectives. (Best for Qualitative)" },
          { label: "C", text: "I need to combine numbers with personal insights. (Best for Mixed Methods)" },
        ],
      },
      {
        prompt: "The nature of your research problem often determines the best approach. Which statement best fits your study?",
        options: [
          { label: "A", text: "I need to identify factors that influence an outcome. (Best for Quantitative Research)" },
          { label: "B", text: "I need to explore an understudied phenomenon. (Best for Qualitative Research)" },
          { label: "C", text: "I need to combine broad trends with in-depth perspectives. (Best for Mixed Methods Research)" },
        ],
      },
      {
        prompt: "Researchers bring personal experiences into their work. Which best describes your situation?",
        options: [
          { label: "A", text: "I have a strong scientific background, so I prefer structured data and hypotheses. (Quantitative Bias)" },
          { label: "B", text: "I have worked closely with my research subjects and value their perspectives. (Qualitative Bias)" },
          { label: "C", text: "I think both approaches are useful depending on the study. (Mixed Methods Bias)" },
        ],
      },
      {
        prompt: "Consider your research audience. Who are you writing for?",
        options: [
          { label: "A", text: "Scientists, policymakers, or funding agencies who expect statistical data. (Best for Quantitative)" },
          { label: "B", text: "Community groups, educators, or practitioners who value personal insights. (Best for Qualitative)" },
          { label: "C", text: "Both academic and practical audiences who want a well-rounded view. (Best for Mixed Methods)" },
        ],
      },
];

export default function ResearchQuestionsForm({ onComplete, projectName = 'your project' }: ResearchQuestionsFormProps) {
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [responses, setResponses] = useState<Response[]>([]);
  
    const handleOptionSelect = (selectedOption: { label: string; text: string }) => {
      const newResponses = [...responses];
      newResponses[currentQuestionIndex] = {
        question: questions[currentQuestionIndex].prompt,
        answer: selectedOption.text,
      };
      setResponses(newResponses);
      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      } else {
        onComplete(newResponses);
      }
    };
  
    const currentQuestion = questions[currentQuestionIndex];
  
    return (
      <div className="w-full max-w-2xl mx-auto bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
        {currentQuestionIndex === 0 && (
          <div className="mb-6 p-4 bg-indigo-50 rounded-lg border border-indigo-100">
            <h3 className="text-lg font-semibold text-indigo-900 mb-2">
              Determine Research Type for "{projectName}"
            </h3>
            <p className="text-gray-700">
              Please answer the following questions to help us determine the most appropriate research methodology for your project.
            </p>
          </div>
        )}
        
        <h2 className="text-2xl font-semibold text-indigo-900 mb-6">
          {currentQuestion.prompt}
        </h2>
        <div className="space-y-4">
          {currentQuestion.options.map((option) => (
            <button
              key={option.label}
              onClick={() => handleOptionSelect(option)}
              className={`w-full p-3 text-left border rounded-xl hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-black ${
                responses[currentQuestionIndex]?.answer === option.text ? 'bg-indigo-100 border-indigo-500' : 'border-gray-300'
              }`}
            >
              <span className="font-medium">{option.label}.</span> {option.text}
            </button>
          ))}
        </div>
        {currentQuestionIndex > 0 && (
          <button
            onClick={() => setCurrentQuestionIndex(currentQuestionIndex - 1)}
            className="mt-4 text-indigo-600 hover:text-indigo-800 font-medium"
          >
            Back
          </button>
        )}
      </div>
    );
  }