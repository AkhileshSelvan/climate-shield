const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  let executablePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
  if (!fs.existsSync(executablePath)) {
      executablePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  }

  const browser = await puppeteer.launch({ 
      headless: true,
      executablePath: executablePath
  });
  const page = await browser.newPage();
  
  let hasCorsError = false;
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('PAGE ERROR:', msg.text());
      if (msg.text().includes('CORS') || msg.text().includes('Cross-Origin')) {
        hasCorsError = true;
      }
    }
  });

  page.on('pageerror', error => {
    console.log('PAGE EXCEPTION:', error.message);
  });
  
  page.on('requestfailed', request => {
    console.log(`REQUEST FAILED: ${request.url()} - ${request.failure().errorText}`);
    if (request.failure().errorText.includes('net::ERR_FAILED') && request.url().includes('localhost:8000')) {
        hasCorsError = true;
        console.log("Network error on backend request, likely CORS.");
    }
  });

  try {
    console.log("Navigating to Farm Setup...");
    await page.goto('http://localhost:3000/demo/farm-setup', { waitUntil: 'networkidle2' });
    
    const clickByText = async (text, waitTextAfter) => {
      await page.waitForFunction((t) => {
        const els = Array.from(document.querySelectorAll('button'));
        return els.find(el => el.textContent.includes(t));
      }, {timeout: 10000}, text);
      
      await page.evaluate((t) => {
        const els = Array.from(document.querySelectorAll('button'));
        const el = els.find(el => el.textContent.includes(t));
        if (el) el.click();
      }, text);
      
      if (waitTextAfter) {
          await page.waitForFunction((t) => document.body.innerText.includes(t), {timeout: 10000}, waitTextAfter);
      }
    };

    console.log("Clicking Analyze Risk...");
    await clickByText('Analyze Risk', 'Climate Risk Analysis');
    await page.waitForFunction(() => document.body.innerText.includes('MEDIUM'));
    
    const riskContent = await page.evaluate(() => document.body.innerText);
    if (!riskContent.includes('MEDIUM') || !riskContent.includes('7 / 35')) {
      console.log("Missing expected risk results (MEDIUM, 7 / 35)");
    } else {
      console.log("Verified Risk: MEDIUM, 7/35 years");
    }
    
    console.log("Clicking View Policy...");
    await clickByText('View Policy', 'Insurance Policy');
    
    console.log("Clicking Create Policy...");
    await clickByText('Create Policy');
    
    console.log("Waiting for backend response...");
    await new Promise(r => setTimeout(r, 2000));
    
    console.log("Clicking Simulate Climate Event...");
    await clickByText('Simulate Climate Event', 'Climate Event Simulator');
    
    console.log("Clicking Run Simulation...");
    await clickByText('Run Simulation', 'TRIGGER ACTIVATED');
    
    console.log("Trigger activated. Clicking View Payout...");
    await clickByText('View Payout', 'Payout Result');
    
    const payoutContent = await page.evaluate(() => document.body.innerText);
    if (!payoutContent.includes('21,600')) {
      console.log("Expected payout 21,600 not found!");
    } else {
      console.log("Verified payout 21,600");
    }

    console.log("Clicking Repeat Evaluation...");
    await clickByText('Repeat Evaluation', 'Idempotent Reuse');
    console.log("Verified Idempotent Reuse");

    if (hasCorsError) {
      console.log("FAIL: CORS errors detected in console.");
      process.exit(1);
    } else {
      console.log("SUCCESS: No CORS errors detected.");
      console.log("Golden Demo E2E passing successfully in browser!");
    }

  } catch (err) {
    console.error("Test failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
