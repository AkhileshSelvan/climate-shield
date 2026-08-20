export const translations = {
  en: {
    "Farm Setup": "Farm Setup",
    "Risk Analysis": "Climate Risk Analysis",
    "Policy Details": "Insurance Policy",
    "Simulate Climate Event": "Climate Event Simulator",
    "Payout Evaluation": "Payout Result",
    "Continue — Analyze Risk": "Analyze Risk",
    "Continue — Review Policy": "View Policy",
    "Create Policy": "Create Policy",
    "Run Simulation": "Run Simulation",
    "View Payout": "View Payout",
    "risk_read_aloud": "Risk analysis complete. Risk level is {level}. The expected trigger frequency is {freq} percent.",
    "simulate_read_aloud_trigger": "Simulation complete. Trigger activated.",
    "simulate_read_aloud_no_trigger": "Simulation complete. Trigger not activated.",
  },
  ta: {
    "Farm Setup": "பண்ணை அமைப்பு (Farm Setup)",
    "Risk Analysis": "ஆபத்து பகுப்பாய்வு (Risk Analysis)",
    "Policy Details": "பாலிசி விவரங்கள் (Policy Details)",
    "Simulate Climate Event": "காலநிலை நிகழ்வு உருவகப்படுத்துதல் (Simulate Climate Event)",
    "Payout Evaluation": "பணம் செலுத்தும் மதிப்பீடு (Payout Evaluation)",
    "Continue — Analyze Risk": "தொடரவும் — ஆபத்தை பகுப்பாய்வு செய்",
    "Continue — Review Policy": "தொடரவும் — பாலிசியை மதிப்பாய்வு செய்",
    "Create Policy": "பாலிசியை உருவாக்கு",
    "Run Simulation": "உருவகப்படுத்துதலை இயக்கவும்",
    "View Payout": "பணம் செலுத்துதலைக் காண்க",
    "risk_read_aloud": "ஆபத்து பகுப்பாய்வு முடிந்தது. ஆபத்து நிலை {level}. எதிர்பார்க்கப்படும் தூண்டுதல் அதிர்வெண் {freq} சதவீதம்.",
    "simulate_read_aloud_trigger": "உருவகப்படுத்துதல் முடிந்தது. தூண்டுதல் செயல்படுத்தப்பட்டது.",
    "simulate_read_aloud_no_trigger": "உருவகப்படுத்துதல் முடிந்தது. தூண்டுதல் செயல்படுத்தப்படவில்லை.",
  }
};

export type TranslationKey = keyof typeof translations.en;
