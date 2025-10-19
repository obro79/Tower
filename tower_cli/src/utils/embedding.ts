import OpenAI from 'openai';
import * as fs from 'fs';
import * as path from 'path';
import { Logger } from './logger.js';

const EMBEDDING_MODEL = 'text-embedding-3-small';
const EMBEDDING_DIMENSION = 1536;

let openaiClient: OpenAI | null = null;

function getOpenAIClient(): OpenAI {
  if (!openaiClient) {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      throw new Error('OPENAI_API_KEY environment variable is not set');
    }
    openaiClient = new OpenAI({ apiKey });
  }
  return openaiClient;
}

export async function generateEmbeddingFromText(text: string): Promise<number[]> {
  if (!text || text.trim().length === 0) {
    throw new Error('Cannot generate embedding from empty text');
  }

  try {
    const client = getOpenAIClient();
    
    const response = await client.embeddings.create({
      model: EMBEDDING_MODEL,
      input: text,
      encoding_format: 'float',
    });

    const embedding = response.data[0].embedding;
    
    if (embedding.length !== EMBEDDING_DIMENSION) {
      throw new Error(`Expected ${EMBEDDING_DIMENSION} dimensions, got ${embedding.length}`);
    }

    return embedding;
  } catch (error: any) {
    Logger.error(`Failed to generate embedding from text: ${error.message}`);
    throw error;
  }
}

export async function generateEmbeddingFromFile(filePath: string): Promise<number[]> {
  if (!fs.existsSync(filePath)) {
    throw new Error(`File not found: ${filePath}`);
  }

  const stats = fs.statSync(filePath);
  
  if (stats.size > 10 * 1024 * 1024) {
    Logger.warning(`File ${path.basename(filePath)} is large (${(stats.size / 1024 / 1024).toFixed(2)} MB), reading first 100KB for embedding`);
  }

  try {
    let fileContent: string;
    
    try {
      const maxBytes = Math.min(stats.size, 100 * 1024);
      const buffer = Buffer.alloc(maxBytes);
      const fd = fs.openSync(filePath, 'r');
      fs.readSync(fd, buffer, 0, maxBytes, 0);
      fs.closeSync(fd);
      
      fileContent = buffer.toString('utf-8');
    } catch (decodeError) {
      const fileName = path.basename(filePath);
      const fileExt = path.extname(filePath);
      fileContent = `${fileName} ${fileExt} binary file`;
      Logger.warning(`Binary file detected: ${fileName}, using filename for embedding`);
    }

    if (!fileContent || fileContent.trim().length === 0) {
      const fileName = path.basename(filePath);
      fileContent = `empty file ${fileName}`;
    }

    return await generateEmbeddingFromText(fileContent);
  } catch (error: any) {
    Logger.error(`Failed to generate embedding from file: ${error.message}`);
    throw error;
  }
}

export function isEmbeddingEnabled(): boolean {
  const envVar = process.env.TOWER_ENABLE_EMBEDDINGS;
  if (envVar !== undefined) {
    return envVar.toLowerCase() === 'true' || envVar === '1';
  }
  return true;
}
