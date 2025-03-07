import { Mistral } from '@mistralai/mistralai';
import fs from 'fs';

const apiKey = process.env.MISTRAL_API_KEY;

const client = new Mistral({apiKey: apiKey});

const training_file = fs.readFileSync('training_file.jsonl');
const training_data = await client.files.upload({
    file: {
        fileName: "training_file.jsonl",
        content: training_file,
    }
});

const validation_file = fs.readFileSync('validation_file.jsonl');
const validation_data = await client.files.upload({
    file: {
        fileName: "validation_file.jsonl",
        content: validation_file,
    }
});

const createdJob = await client.fineTuning.jobs.create({
    model: 'open-mistral-7b',
    trainingFiles: [{fileId: training_data.id, weight: 1}],
    validationFiles: [validation_data.id],
    hyperparameters: {
      trainingSteps: 10,
      learningRate: 0.0001,
    },
    autoStart:false,
  });

await client.fineTuning.jobs.start({jobId: createdJob.id})

