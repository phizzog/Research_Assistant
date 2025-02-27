// app/page.tsx
'use client';

import { useState } from 'react';
import ResearchForm from '@/components/ResearchForm';
import ResearchQuestionsForm from '@/components/ResearchQuestionsForm';

interface Response {
  question: string;
  answer: string;
}

export default function Home() {
  const [step, setStep] = useState(1);
  const [projectDetails, setProjectDetails] = useState({ title: '', description: '' });

  const handleProjectSubmit = (details: string) => {
    const [title, description] = details.split('\n\nResearch Description:\n');
    setProjectDetails({ title: title.replace('Project Title: ', ''), description });
    setStep(2);
  };

  const handleQuestionsComplete = (responses: Response[]) => {
    const fullData = {
      "research title": projectDetails.title,
      "research description": projectDetails.description,
      ...responses.reduce((acc, resp, index) => {
        acc[`question ${index + 1}`] = resp.question;
        acc[`answer ${index + 1}`] = resp.answer;
        return acc;
      }, {} as Record<string, string>),
    };
    console.log('Full research data:', fullData);
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gray-50">
      {step === 1 && <ResearchForm onSubmit={handleProjectSubmit} />}
      {step === 2 && <ResearchQuestionsForm onComplete={handleQuestionsComplete} />}
    </main>
  );
}