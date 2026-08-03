import { GoogleGenAI, Type } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || "" });

export interface Lead {
  srNo: number;
  name: string;
  title: string;
  company: string;
  email: string;
  phone: string;
  website: string;
  location: string;
  linkedIn: string;
}

export async function generateLeads(
  productName: string,
  sku: string,
  brand: string,
  category?: string,
  type?: string,
  name?: string,
  division?: string,
  description?: string
): Promise<Lead[]> {
  const prompt = `Act as a senior B2B market researcher specializing in FMCG, consumer electronics, electrical trading, and distribution networks in the GCC region.

Your task is to identify REAL companies and VERIFIED decision-makers who are potential buyers, distributors, or bulk purchasers.

Product Context:
* Product Name: ${productName}
${division ? `* Division: ${division}` : ""}
${brand ? `* Brand: ${brand}` : ""}
${description ? `* Product Description: ${description}` : ""}
${sku ? `* SKU: ${sku}` : ""}

If the product relates to batteries, use battery-focused search logic.
If the product relates to lighting (LED, OSRAM, etc.), adapt to electrical and lighting buyers.

Target Product Keywords (AUTO-EXPAND based on product):
* Use variations and related keywords derived from product name

Target Regions:
UAE, Saudi Arabia, Qatar, Oman, Kuwait

Target Industries:
* Distributors
* Electrical trading companies
* Electronics distributors
* Retail chains / supermarkets
* Industrial suppliers
* MRO suppliers
* Contractors (for lighting products)

Target Buyer Roles:
Procurement Manager
Purchase Manager
Supply Chain Manager
Category Manager
Buying Manager
Sales Manager (Distributor level)
Business Development Manager
General Manager

Search Strategy:
* Combine product keywords + distributor/supplier
* Combine buyer role + company + region
* Include competitor-based search (e.g., Duracell, Energizer for batteries)

STRICT RULES:
* DO NOT invent or guess names, emails, or phone numbers
* Only include verifiable professionals (LinkedIn, company websites, directories)
* Avoid duplicates
* Avoid generic emails unless necessary
* Prioritize high-relevance companies

OUTPUT FORMAT (STRICT JSON):
Return a JSON array of objects with keys: name, title, company, email, phone, website, location, linkedIn.

Minimum Leads Required: 30–50`;

  try {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-latest",
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.ARRAY,
          items: {
            type: Type.OBJECT,
            properties: {
              name: { type: Type.STRING },
              title: { type: Type.STRING },
              company: { type: Type.STRING },
              email: { type: Type.STRING },
              phone: { type: Type.STRING },
              website: { type: Type.STRING },
              location: { type: Type.STRING },
              linkedIn: { type: Type.STRING },
            },
            required: ["name", "title", "company", "email", "phone", "website", "location", "linkedIn"],
          },
        },
      },
    });

    const text = response.text;
    if (!text) return [];
    
    const rawLeads = JSON.parse(text);
    return rawLeads.map((lead: any, index: number) => ({
      ...lead,
      srNo: index + 1,
    }));
  } catch (error) {
    console.error("Gemini API Error:", error);
    throw error;
  }
}
