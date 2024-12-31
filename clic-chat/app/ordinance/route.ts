import { NextRequest } from "next/server";
import * as lancedb from "@lancedb/lancedb";
import { AzureOpenAI } from "openai";
import dotenv from 'dotenv';

import {
  TextEmbeddingFunction,
  getRegistry,
  register,
} from "@lancedb/lancedb/embedding";

dotenv.config();

const deployment = "embedding";
const endpoint = process.env.AZURE_OPENAI_ENDPOINT;
const apiVersion = process.env.AZURE_OPENAI_API_VERSION;
const key = process.env.AZURE_OPENAI_KEY;
const client = new AzureOpenAI({apiKey: key,  endpoint : endpoint, deployment: deployment, apiVersion: apiVersion });

const db = await lancedb.connect("@/../../db");
// const registry = getRegistry();

// @register("azure-openai")
// class AzureOpenAIEmbedding extends TextEmbeddingFunction {
//   name = "azure-openai";
//   #ndims!: number;
//   client: AzureOpenAI | undefined;
//
//   async init() {
//     this.client = new AzureOpenAI({apiKey: key, endpoint: endpoint, deployment: deployment, apiVersion: apiVersion});
//     this.#ndims = await this.generateEmbeddings(["hello"]).then(
//       (e) => e[0].length,
//     );
//   }
//
//   ndims() {
//     return this.#ndims;
//   }
//
//   toJSON() {
//     return {
//       name: this.name,
//     };
//   }
//
//   async generateEmbeddings(texts: string[]) {
//     const output = await this.client?.embeddings.create({input: texts, model: "embedding"});
//     const embeddings = output?.data.map((e) => e.embedding);
//     if (!embeddings) throw new Error("No embeddings found");
//     return embeddings;
//   }
// }
//


export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.get("q");
  if (!query) return new Response("Please provide a search query");

  const tbl = await db.openTable("ordinances");

  return registry.get("azure-openai");

  const _res = await tbl
    .search(query, "vector")
    .select(["text"])
    .limit(10)
    .toArray();

  return new Response(
    `You searched for ${query}\n ${JSON.stringify(_res, null, 2)}`,
  );
}
