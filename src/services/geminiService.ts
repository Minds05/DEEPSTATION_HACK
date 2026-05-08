import { GoogleGenAI } from "@google/genai";
import { AgentType, UserProfile } from "../types";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || '' });

function extractJson(text: string) {
  try {
    // Try to find the first '{' and corresponding last '}'
    const start = text.indexOf('{');
    const end = text.lastIndexOf('}');
    if (start !== -1 && end !== -1 && end > start) {
      return JSON.parse(text.substring(start, end + 1));
    }
    return JSON.parse(text);
  } catch (error) {
    console.error("JSON extraction failed:", error, "Raw text:", text);
    throw error;
  }
}

export async function analyzeCommunityIssue(issue: string, history: { role: 'user' | 'assistant', content: string }[] = [], sessionAgent: AgentType | null = null, userProfile: UserProfile | null = null) {
  const model = "gemini-3-flash-preview";
  
  const historyContext = history.map(h => `${h.role === 'user' ? 'User' : 'Assistant'}: ${h.content}`).join('\n');

  const userContext = userProfile ? `
    User Profile (Loaded from Resume):
    - Name: ${userProfile.name}
    - Email: ${userProfile.email}
    - Skills: ${userProfile.skills.join(', ')}
    - Experience: ${userProfile.experience}
    - Education: ${userProfile.education}
  ` : "No user profile provided.";

  const prompt = `
    You are the CivicNexus Master Orchestrator.
    Your primary goal is to CLASSIFY the community issue and SELECTIVELY DELEGATE to the specific agent(s) that are strictly necessary. 

    ${userContext}

    Conversation History Context:
    ${historyContext}

    Current Contextual Specialist: ${sessionAgent || 'None assigned yet'}

    Instructions:
    1. DIRECTLY ADDRESS the user's issue. Use professional, civic-minded language.
    2. USE CLEAR MARKDOWN STRUCTURE:
       - Use \`###\` for main headers.
       - Use horizontal rules \`---\` to separate logical sections.
       - CRITICAL: Markdown tables MUST HAVE NEWLINES. Every row of a table must be on a new line. 
       - Ensure tables have empty lines before and after them.
    3. If the user asks to "apply" or "suggest jobs" and their profile is available:
       - Match the "Skills" and "Experience" against available civic roles.
       - Provide a \`### 🤖 MATCHED CIVIC OPPORTUNITIES\` table with columns: | Role | Organization | Match Reason |
       - Generate a \`### 📝 PROPOSED APPLICATION SUMMARY\` section.
       - Use \`**Field:** Value\` on separate lines for form details.
    4. If a "Current Contextual Specialist" is already assigned, prioritize using that agent.
    5. Provide the output in the "details" field.
    6. RESIST meta-commentary like "I have analyzed...". Just provide the results.

    Current Input: "${issue}"

    Return the analysis in JSON format:
    {
      "summary": "Short overview",
      "steps": [
        { "agent": "AgentName", "task": "Task description", "details": "Specific implementation details or the actual Answer" }
      ],
      "estimatedImpact": "Description of expected outcome"
    }
  `;

  try {
    const response = await ai.models.generateContent({
      model,
      contents: prompt,
      config: {
        responseMimeType: "application/json"
      }
    });
    
    return extractJson(response.text || "{}");
  } catch (error) {
    console.error("Analysis failed:", error);
    return null;
  }
}

export async function processResume(resumeData: string | { data: string, mimeType: string }): Promise<UserProfile | null> {
  const model = "gemini-3-flash-preview";
  
  const contentPart = typeof resumeData === 'string' 
    ? { text: `Analyze the following resume text:\n${resumeData}` }
    : { inlineData: { data: resumeData.data, mimeType: resumeData.mimeType } };

  const prompt = `
    Analyze the provided resume and extract the user's professional profile.
    If the document is a PDF or image, use your visual understanding to extract the text first.
    
    Return the profile in JSON format with exactly these fields:
    {
      "name": "Full Name",
      "email": "Email Address",
      "phone": "Phone Number",
      "skills": ["Skill 1", "Skill 2"],
      "education": "Brief description of education",
      "experience": "Brief summary of work history"
    }
  `;

  try {
    const response = await ai.models.generateContent({
      model,
      contents: {
        parts: [
          contentPart,
          { text: prompt }
        ]
      },
      config: {
        responseMimeType: "application/json"
      }
    });
    
    const profile = extractJson(response.text || "{}");
    return {
      name: profile.name || '',
      email: profile.email || '',
      phone: profile.phone || '',
      skills: Array.isArray(profile.skills) ? profile.skills : [],
      education: profile.education || '',
      experience: profile.experience || '',
      resumeText: typeof resumeData === 'string' ? resumeData : "[Binary Document]"
    };
  } catch (error) {
    console.error("Resume processing failed:", error);
    return null;
  }
}

export async function libraryQA(bookContext: string, question: string) {
  const model = "gemini-3-flash-preview";
  const prompt = `
    You are the AssetAgent (Library & Resource specialized).
    Use the following book context to answer the user's question accurately.
    Context: ${bookContext}
    Question: ${question}
  `;

  try {
    const response = await ai.models.generateContent({
      model,
      contents: prompt
    });
    return response.text;
  } catch (error) {
    console.error("Library Q&A failed:", error);
    return "Error retrieving answer from library archives.";
  }
}
