const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

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
  
  // Intercept speech synthesis to verify Read Aloud
  await page.evaluateOnNewDocument(() => {
    window.speechSynthesisLogs = [];
    const originalSpeak = window.speechSynthesis.speak;
    window.speechSynthesis.speak = function(utterance) {
      window.speechSynthesisLogs.push({ text: utterance.text, lang: utterance.lang });
      originalSpeak.call(window.speechSynthesis, utterance);
    };
  });

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
      } else {
          await new Promise(r => setTimeout(r, 2000));
      }
  };

  try {
    console.log("Navigating to Farm Setup...");
    await page.goto('http://localhost:3000/demo/farm-setup', { waitUntil: 'networkidle0' });

    console.log("Verifying English text...");
    let content = await page.evaluate(() => document.body.innerText);
    if (!content.includes('Farm Setup')) throw new Error('Farm Setup missing');

    console.log("Toggling to Tamil...");
    const toggleButton = await page.$('button[aria-label="Toggle language"]');
    await toggleButton.click();
    await new Promise(r => setTimeout(r, 1000));
    content = await page.evaluate(() => document.body.innerText);
    if (!content.includes('பண்ணை அமைப்பு')) throw new Error('Tamil Farm Setup missing');

    console.log("Toggling back to English...");
    await toggleButton.click();
    await new Promise(r => setTimeout(r, 1000));

    console.log("Proceeding to Risk Analysis...");
    await clickByText('Analyze Risk', 'Climate Risk Analysis');
    
    console.log("Waiting for risk data...");
    await page.waitForFunction(() => document.body.innerText.includes('MEDIUM'), {timeout: 15000});

    console.log("Verifying Status Symbols...");
    content = await page.evaluate(() => document.body.innerText);
    if (!content.includes('MEDIUM') || !content.includes('🟡')) {
        console.log("Missing MEDIUM or 🟡");
    } else {
        console.log("Found MEDIUM symbol!");
    }
    if (!content.includes('sufficient') || !content.includes('✅')) {
        console.log("Missing sufficient or ✅");
    } else {
        console.log("Found sufficient symbol!");
    }

    console.log("Verifying Read Aloud on Risk Analysis...");
    const readAloudButtons = await page.$$('button[aria-label="Read Aloud"]');
    if (readAloudButtons.length > 0) {
        await readAloudButtons[0].click();
        await new Promise(r => setTimeout(r, 500));
        const logs = await page.evaluate(() => window.speechSynthesisLogs);
        console.log("SpeechSynthesis logs:", logs);
    } else {
        throw new Error("Read Aloud button not found!");
    }

    console.log("Proceeding to Simulate Climate Event...");
    await clickByText('View Policy', 'Insurance Policy');
    await clickByText('Create Policy');
    await new Promise(r => setTimeout(r, 3000)); // wait for api
    await clickByText('Simulate Climate Event', 'Climate Event Simulator');

    console.log("Testing Near Miss (non-triggering) via API Mock...");
    await page.setRequestInterception(true);
    page.on('request', request => {
        if (request.url().includes('simulate')) {
            if (request.method() === 'OPTIONS') {
                request.respond({
                    status: 204,
                    headers: {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
                        "Access-Control-Allow-Headers": "*"
                    }
                });
            } else {
                request.respond({
                    status: 200,
                    content: 'application/json',
                    headers: {"Access-Control-Allow-Origin": "*"},
                    body: JSON.stringify({
                        policy_id: 1,
                        trigger_type: "drought",
                        observed_rainfall_mm: 30,
                        threshold_mm: 20,
                        triggered: false,
                        payout_amount: 0,
                        notes: "Mock non-trigger for test"
                    })
                });
            }
        } else {
            request.continue();
        }
    });
    
    await clickByText('Run Simulation', 'No Trigger');
    
    console.log("Verifying Near Miss Explainer...");
    content = await page.evaluate(() => document.body.innerText);
    if (content.includes('Near Miss Analysis') && content.includes('10.0mm')) {
        console.log("Near Miss explainer found and correct!");
    } else {
        throw new Error("Near Miss explainer not found or incorrect");
    }

    console.log("Verifying Read Aloud on Simulate...");
    const readAloudButtons2 = await page.$$('button[aria-label="Read Aloud"]');
    if (readAloudButtons2.length > 0) {
        await readAloudButtons2[0].click();
        await new Promise(r => setTimeout(r, 500));
        const logs = await page.evaluate(() => window.speechSynthesisLogs);
        console.log("SpeechSynthesis logs after simulate:", logs);
    } else {
        throw new Error("Read Aloud button not found on Simulate!");
    }

    console.log("UX Verification passed successfully!");
  } catch (err) {
      console.error("Test failed:", err);
  } finally {
      await browser.close();
  }
})();
