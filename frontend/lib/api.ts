const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function chat(query: string) {
  const response = await fetch(`${NEXT_PUBLIC_API_URL}/chat?query=${encodeURIComponent(query)}`);
  if (!response.ok) {
    throw new Error("Failed to fetch chat response");
  }
  return response.json();
}
