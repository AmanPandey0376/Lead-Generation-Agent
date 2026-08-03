import OpenAI from "openai";

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY || "",
    dangerouslyAllowBrowser: true
});

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
    segment: string;
    priority: string;
    channel: string;
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
* grocery stores
* dropshipping platforms
* ecommerce aggregators
* fulfillment centres
* Ecommerce resellers

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
Return a JSON object containing a "leads" array. Each object in the "leads" array MUST have the exact keys: name, title, company, email, phone, website, location, linkedIn, segment (e.g. Retail, Healthcare, Construction), priority (High, Medium, Low), channel (e.g. Distributor, End User, Wholesaler).

Minimum Leads Required: 30–50`;

    try {
        const response = await openai.chat.completions.create({
            model: "gpt-4o",
            messages: [
                {
                    role: "user",
                    content: prompt,
                },
            ],
            response_format: { type: "json_object" },
        });

        const text = response.choices[0]?.message?.content;
        if (!text) return [];

        // Parse the JSON object securely and extract the leads array
        const rawData = JSON.parse(text);

        let rawLeads: any[] = [];
        if (Array.isArray(rawData)) {
            rawLeads = rawData;
        } else if (rawData.leads && Array.isArray(rawData.leads)) {
            rawLeads = rawData.leads;
        } else {
            // Fallback: look for the first array in the JSON values
            const arrayValue = Object.values(rawData).find(val => Array.isArray(val));
            if (arrayValue) {
                rawLeads = arrayValue as any[];
            }
        }

        // Filter against existing PostgreSQL database leads to avoid duplicates
        try {
            const filterResponse = await fetch("/api/filter-existing-leads", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ leads: rawLeads })
            });
            if (filterResponse.ok) {
                const filterData = await filterResponse.json();
                rawLeads = filterData.uniqueLeads;
            }
        } catch (dbError) {
            console.error("Could not filter against database", dbError);
        }

        return rawLeads.map((lead: any, index: number) => ({
            ...lead,
            srNo: index + 1,
        }));
    } catch (error) {
        console.error("OpenAI API Error:", error);
        throw error;
    }
}
