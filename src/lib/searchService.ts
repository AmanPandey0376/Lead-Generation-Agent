export interface SearchResult {
  title: string;
  snippet: string;
  url: string;
}

export interface SearchProvider {
  search(query: string): Promise<SearchResult[]>;
}

/**
 * Serper API search provider implementation.
 */
export class SerperSearchProvider implements SearchProvider {
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async search(query: string): Promise<SearchResult[]> {
    if (!this.apiKey) {
      console.warn("Serper Search API key is not configured.");
      return [];
    }

    try {
      // Use native global fetch available in Node.js 18+
      const response = await fetch("https://google.serper.dev/search", {
        method: "POST",
        headers: {
          "X-API-KEY": this.apiKey,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          q: query,
          num: 15, // Retrieve top 15 results
        }),
      });

      if (!response.ok) {
        throw new Error(`Serper search failed: ${response.status} ${response.statusText}`);
      }

      const data: any = await response.json();
      const results: SearchResult[] = [];

      // Extract organic search results
      if (data.organic && Array.isArray(data.organic)) {
        for (const item of data.organic) {
          results.push({
            title: item.title || "",
            snippet: item.snippet || "",
            url: item.link || "",
          });
        }
      }

      // Extract place search results (Google Maps business listings) if they exist
      if (data.places && Array.isArray(data.places)) {
        for (const place of data.places) {
          results.push({
            title: place.title || place.name || "",
            snippet: `Address: ${place.address || ""}. Phone: ${place.phoneNumber || ""}. Rating: ${place.rating || ""}.`,
            url: place.website || place.link || "",
          });
        }
      }

      return results;
    } catch (error) {
      console.error(`Serper search failed for query "${query}":`, error);
      return [];
    }
  }
}

/**
 * Searches across multiple keywords and aggregates the deduplicated results.
 */
export async function discoverCompanies(keywords: string[]): Promise<SearchResult[]> {
  const apiKey = process.env.SERPER_API_KEY || "";
  if (!apiKey) {
    console.warn("SERPER_API_KEY environment variable is not defined.");
  }

  const provider = new SerperSearchProvider(apiKey);
  
  // Aggregate queries for the first few high-value keywords to discover a rich list of companies
  const targetKeywords = keywords.slice(0, 5);
  const searchPromises = targetKeywords.map((kw) => provider.search(kw));
  const resultsList = await Promise.all(searchPromises);

  const allResults: SearchResult[] = [];
  const seenUrls = new Set<string>();

  for (const results of resultsList) {
    for (const res of results) {
      if (!res.url || res.url.trim() === "") continue;

      // Normalize URL to avoid duplicates (strip trailing slash, query parameters, and protocol)
      let normalized = res.url.trim().toLowerCase();
      try {
        const urlObj = new URL(normalized);
        normalized = urlObj.hostname + urlObj.pathname;
      } catch (e) {
        // Fallback simple normalization
        normalized = normalized.replace(/^(https?:\/\/)?(www\.)?/, "");
      }
      
      if (normalized.endsWith("/")) {
        normalized = normalized.slice(0, -1);
      }

      if (!seenUrls.has(normalized)) {
        seenUrls.add(normalized);
        allResults.push(res);
      }
    }
  }

  return allResults;
}
