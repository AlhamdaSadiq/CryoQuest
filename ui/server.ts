import express from 'express';
import path from 'path';
import fs from 'fs';
import { spawn } from 'child_process';
import { createServer as createViteServer } from 'vite';
import { GoogleGenAI } from '@google/genai';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env.local') });
dotenv.config();

// Absolute path to the Python "lunar_ice_detection" project. Since this UI
// now lives at lunar_ice_detection/ui, the pipeline root is one level up by
// default. Override with PIPELINE_DIR in .env if you've moved it elsewhere.
const PIPELINE_DIR = path.resolve(
  process.env.PIPELINE_DIR || path.join(process.cwd(), '..')
);
const PIPELINE_OUTPUT = path.join(PIPELINE_DIR, 'data', 'output');
const PYTHON_BIN = process.env.PYTHON_BIN || 'python3';

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // Lazy Initialize Gemini SDK
  const getAi = () => {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      throw new Error('GEMINI_API_KEY is not configured');
    }
    return new GoogleGenAI({
      apiKey,
      httpOptions: {
        headers: {
          'User-Agent': 'aistudio-build',
        },
      },
    });
  };

  // API Routes
  app.get('/api/health', (_req, res) => {
    res.json({ status: 'ok', time: new Date().toISOString() });
  });

  // ---------------------------------------------------------------------
  // Lunar Ice Detection pipeline bridge
  // ---------------------------------------------------------------------

  // Pipeline availability / last-run status
  app.get('/api/pipeline/status', (_req, res) => {
    const iceProbTif = path.join(PIPELINE_OUTPUT, 'fusion', 'fusion_ice_probability.tif');
    const previewPng = path.join(PIPELINE_OUTPUT, 'fusion', 'fusion_ice_probability_preview.png');
    const volumeJson = path.join(PIPELINE_OUTPUT, 'volume', 'volume_estimate.json');
    const exists = (p: string) => fs.existsSync(p);
    res.json({
      pipelineDir: PIPELINE_DIR,
      pipelineDirFound: exists(PIPELINE_DIR),
      hasFusionOutput: exists(iceProbTif),
      hasPreviewPng: exists(previewPng),
      hasVolumeEstimate: exists(volumeJson),
      lastModified: exists(volumeJson) ? fs.statSync(volumeJson).mtime : null,
    });
  });

  // Ranked landing-site shortlist, straight from the pipeline's output dir
  app.get('/api/pipeline/landing-sites', (_req, res) => {
    const file = path.join(PIPELINE_OUTPUT, 'planning', 'landing_site_shortlist.geojson');
    if (!fs.existsSync(file)) {
      res.status(404).json({ error: 'landing_site_shortlist.geojson not found. Run the pipeline first.' });
      return;
    }
    res.sendFile(file);
  });

  // Maxwell-Garnett subsurface ice-volume estimate
  app.get('/api/pipeline/volume-estimate', (_req, res) => {
    const file = path.join(PIPELINE_OUTPUT, 'volume', 'volume_estimate.json');
    if (!fs.existsSync(file)) {
      res.status(404).json({ error: 'volume_estimate.json not found. Run the pipeline first.' });
      return;
    }
    res.sendFile(file);
  });

  // Rendered PNG preview of the fused ice-probability raster
  app.get('/api/pipeline/ice-probability-map.png', (_req, res) => {
    const file = path.join(PIPELINE_OUTPUT, 'fusion', 'fusion_ice_probability_preview.png');
    if (!fs.existsSync(file)) {
      res
        .status(404)
        .json({ error: 'Preview PNG not found. Run the pipeline, then scripts/render_preview_png.py.' });
      return;
    }
    res.sendFile(file);
  });

  // Trigger a full pipeline re-run (main.py) followed by the PNG preview
  // render step. Streams combined stdout/stderr back as plain text.
  app.post('/api/pipeline/run', (_req, res) => {
    if (!fs.existsSync(PIPELINE_DIR)) {
      res.status(404).json({ error: `Pipeline directory not found: ${PIPELINE_DIR}` });
      return;
    }

    res.setHeader('Content-Type', 'text/plain; charset=utf-8');
    res.write(`Running pipeline in ${PIPELINE_DIR}\n`);

    const env = { ...process.env, PYTHONPATH: path.join(PIPELINE_DIR, 'src') };
    const run = spawn(PYTHON_BIN, ['src/lunar_ice_detection/main.py'], { cwd: PIPELINE_DIR, env });

    run.stdout.on('data', (d) => res.write(d));
    run.stderr.on('data', (d) => res.write(d));

    run.on('close', (code) => {
      if (code !== 0) {
        res.write(`\nPipeline exited with code ${code}\n`);
        res.end();
        return;
      }
      const render = spawn(PYTHON_BIN, ['scripts/render_preview_png.py'], { cwd: PIPELINE_DIR, env });
      render.stdout.on('data', (d) => res.write(d));
      render.stderr.on('data', (d) => res.write(d));
      render.on('close', (renderCode) => {
        res.write(`\nDone (pipeline=${code}, preview render=${renderCode})\n`);
        res.end();
      });
    });

    run.on('error', (err) => {
      res.write(`\nFailed to launch pipeline: ${err.message}\n`);
      res.end();
    });
  });

  // AI Crater Analysis Endpoint
  app.post('/api/ai/analyze-crater', async (req, res) => {
    try {
      const { lat, lon, band, slope, altitude } = req.body;
      const ai = getAi();

      const prompt = `You are Lunar Command's AI Orbital Tactical Assistant.
Analyze this lunar surface region:
Latitude: ${lat}° N, Longitude: ${lon}° E
Band Overlay: ${band}
Max Slope Gradient: ${slope}°
Altitude: ${altitude} km

Provide a concise tactical assessment formatted in JSON:
{
  "riskLevel": "CRITICAL" | "WARNING" | "LOW",
  "recommendedSpeed": "e.g. 0.4 m/s",
  "summary": "1-2 sentence tactical summary of regolith density, thermal stability, and terrain safety.",
  "recommendedAction": "1 short recommendation for rover trajectory"
}`;

      const response = await ai.models.generateContent({
        model: 'gemini-3.6-flash',
        contents: prompt,
        config: {
          responseMimeType: 'application/json',
          temperature: 0.3,
        },
      });

      const text = response.text || '{}';
      res.json(JSON.parse(text));
    } catch (err: any) {
      console.error('AI Crater Analysis Error:', err);
      // Fallback response if API key is missing or errored
      res.json({
        riskLevel: req.body?.slope > 20 ? 'CRITICAL' : 'WARNING',
        recommendedSpeed: '0.5 m/s',
        summary: `Regolith density at ${req.body?.lat || 42.12}°N ${req.body?.lon || 18.45}°E requires low-torque crawl. Steep inner crater wall detected.`,
        recommendedAction: 'Engage differential lock and descend along South-East ridge.',
      });
    }
  });

  // AI Diagnostic Query Endpoint
  app.post('/api/ai/diagnostics', async (req, res) => {
    try {
      const { query } = req.body;
      const ai = getAi();

      const response = await ai.models.generateContent({
        model: 'gemini-3.6-flash',
        contents: `You are Sector-7 Lunar Command AI Diagnostic Sub-System. Answer the following mission question concisely in high-utility military technical style:\n\n${query}`,
        config: {
          systemInstruction: 'Keep responses under 120 words. Use technical terms like S-Band, UHF relay, regolith traction, telemetry, and RCS thrusters.',
        },
      });

      res.json({ answer: response.text });
    } catch (err: any) {
      console.error('AI Diagnostics Error:', err);
      res.json({
        answer: 'Sector-7 Diagnostics Online. Systems operating within nominal parameters. S-Band LOS relay standard. Differential drive locked.',
      });
    }
  });

  // Vite middleware in dev mode
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (_req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Lunar Command server running on http://localhost:${PORT}`);
  });
}

startServer();
