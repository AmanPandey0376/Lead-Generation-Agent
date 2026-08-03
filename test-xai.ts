import OpenAI from "openai";

const xai = new OpenAI({
    apiKey: "xai-test",
    baseURL: "http://localhost:3000/xai-api/v1"
});

async function main() {
    try {
        await xai.chat.completions.create({
            model: "grok-4.20-0309-reasoning",
            messages: [{ role: "user", content: "hello" }]
        });
    } catch (e: any) {
        console.log("Error status:", e.status);
        console.log("Error message:", e.message);
    }
}
main();
