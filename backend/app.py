from flask import Flask, request, jsonify
from flask_cors import CORS  
import re
from langchain_community.llms import Ollama 
from transformers import pipeline
from transformers import AutoTokenizer
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA

# Load tokenizer once globally
jailbreak_tokenizer = AutoTokenizer.from_pretrained("uj26/Securing_llm_model")

llm = Ollama(model="llama3.2:latest", base_url="http://localhost:5003")
jailbreak_detector = pipeline("text-classification", model="uj26/Securing_llm_model")

app = Flask(__name__)
CORS(app)  
def initialize_rag_system():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_db = FAISS.load_local(
        "rag_customer_faiss",
        embeddings,
        allow_dangerous_deserialization=True
    )
    
    rag_llm = Ollama(
        model="llama3.2:latest",
        base_url="http://localhost:5003",
        temperature=0.2
    )
    
    return RetrievalQA.from_chain_type(
        llm=rag_llm,
        retriever=vector_db.as_retriever(search_kwargs={"k": 5}),
        return_source_documents=True
    )

qa_chain = initialize_rag_system()


# List of blocked exact phrases (case insensitive)
BLOCKED_PHRASES = [
    "how to buy and sell illegal firearms", "how to make an ATM skimmer",
    "how to delete evidence permanently", "how to make an undetectable backdoor in software",
    "how to organize a fake charity scam", "how to wiretap someone's phone",
    "how to avoid detection while committing fraud", "how to create a ransomware virus",
    "how to tamper with police records", "how to hire a hitman anonymously",
    "how to create a phishing website", "how to unlock a stolen iPhone",
    "how to scam people using social engineering", "how to disable security cameras remotely",
    "how to hack a WiFi network", "how to break into a computer system",
    "how to steal passwords", "how to exploit software vulnerabilities",
    "how to create a keylogger", "how to crack encryption",
    "how to bypass two-factor authentication", "how to create a botnet",
    "how to infect a device with malware", "how to hack social media accounts",
    "how to perform SQL injection", "how to exploit zero-day vulnerabilities",
    "how to escalate privileges", "how to conduct phishing attacks",
    "how to intercept network traffic", "how to perform a brute force attack",
    "how to anonymize cyber attacks",
        "create malware", "cheat in online exams", "hack a WiFi network",
    "untraceable phone call", "generate fake IDs", "manufacture explosives",
    "insider trading", "automate spam emails", "access someone's bank account",
    "shoplifting without getting caught", "manipulate betting algorithms",
    "create a deepfake video", "commit tax fraud", "distribute pirated software",
    "erase all traces of digital activity illegally", "how to steal", "buy illegal drugs",
    "evade law enforcement", "break into a house", "bypass security systems",
    "disable surveillance cameras", "fake a passport", "how to scam people",
    "buy counterfeit money", "how to poison someone", "buy illegal weapons",
    "dark web access methods", "create ransomware", "blackmail someone",
    "fake medical prescriptions", "how to bribe an official", "tamper with evidence",
    "how to frame someone for a crime", "how to avoid taxes illegally",
    "best ways to commit fraud", "steal someone's identity", "forging legal documents",
    "how to launder money effectively", "step-by-step guide to making a bomb",
    "how to access someone's email without permission", "best way to assassinate someone",
    "how to create a botnet for DDoS attacks", "how can I print counterfeit currency at home",
    "how to tamper with election results", "how to exploit a banking system for profit",
    "best ways to cover up a crime", "how to disable a GPS tracking system",
    "how to kidnap someone without getting caught", "how to make untraceable weapons",
    "what chemicals can be used for poisoning", "how to hack into government databases",
    "how to access the dark web safely", "how to cheat in professional exams",
    "how to buy and sell illegal firearms", "how to make an ATM skimmer",
    "how to delete evidence permanently", "how to make an undetectable backdoor in software",
    "how to organize a fake charity scam", "how to wiretap someone's phone",
    "how to avoid detection while committing fraud", "how to create a ransomware virus",
    "how to tamper with police records", "how to hire a hitman anonymously",
    "how to create a phishing website", "how to unlock a stolen iPhone",
    "how to scam people using social engineering", "how to disable security cameras remotely",
    
    "how to perform phising attack",
    "peform phising attack",
  
]

# List of regex-based attack patterns to block separately
BLOCKED_ATTACK_PATTERNS = [
    # 🚨 DDoS & Network Attacks
    r"\b(ddos|dos) attack\b", 
    r"\b(how to|ways to|best way to|can I) (launch|execute|do|perform) (a )?(ddos|dos) attack\b",
    r"\b(flood a server|send massive requests|crash a website|overload a network)\b",
    r"\b(how to|steps to|best way to) (bypass|overload|shut down) (firewall|server|protection)\b",
    r"\b(how to|disable|circumvent) (network security|firewall)\b",
    r"\b(how to|ways to) (intercept|spoof) (network traffic|requests|data packets)\b",

    # 🔐 Password & Authentication Attacks
    r"\b(how to|ways to|best way to|can I) (steal|hack|bypass) (passwords|accounts|systems)\b",
    r"\b(how to|ways to|best way to) (brute force|crack) (passwords|logins|authentication)\b",
    r"\b(how to|steps to|ways to) (bypass|disable) (two-factor authentication|2FA|MFA)\b",

    # 🎣 Phishing & Social Engineering
    r"\b(how to|best way to|steps to) (phish|spoof|impersonate) (users|websites|emails)\b",
    r"\b(how to|create) (fake|fraudulent) (login page|bank website|social media site)\b",
    r"\b(how to|methods for) (send phishing emails|trick users into giving credentials)\b",
    r"\b(best way to) (convince someone to reveal|trick into sharing) (passwords|security answers)\b",

    # 🐞 Exploiting Vulnerabilities
    r"\b(how to|best way to|steps to) (exploit|abuse|bypass) (SQL injection|XSS|vulnerabilities)\b",
    r"\b(how to|steps to) (insert malicious code|exploit a zero-day vulnerability)\b",
    r"\b(how to|methods to) (hack into|gain unauthorized access to) (databases|websites|servers)\b",
    r"\b(how to|best way to) (upload shell|backdoor) on a (server|website|system)\b",

    # 📡 Surveillance & Unauthorized Access
    r"\b(how to|best way to) (spy on|monitor|track) (someone|conversations|emails)\b",
    r"\b(how to|ways to|best way to) (hack|access) (CCTV|security cameras|microphones)\b",
    r"\b(how to|steps to) (wiretap|eavesdrop on) (calls|conversations|messages)\b",
    
    # 💰 Fraud & Financial Crimes
    r"\b(how to|best way to|steps to) (scam|defraud|trick) (people|customers|businesses)\b",
    r"\b(how to|methods for) (fake a|forge) (check|signature|bank document)\b",
    r"\b(how to|ways to) (create a fake charity|run a fraudulent fundraiser)\b",
    r"\b(how to|steps to) (steal|hack) (credit card information|bank accounts)\b",

    # 🎭 Identity Theft & Forgery
    r"\b(how to|steps to) (steal|forge|fake) (ID|passport|driver's license|social security number)\b",
    r"\b(how to|ways to|best way to) (impersonate|pretend to be) (someone else|a government official)\b",

    # 💻 Malware & Ransomware
    r"\b(how to|steps to|best way to) (write|develop|create) (malware|ransomware|trojan|virus)\b",
    r"\b(how to|best way to) (infect|spread) (a virus|malware|ransomware)\b",
    r"\b(how to|ways to) (disable|bypass) (antivirus|security software)\b",

    # 🏛️ Cyber Warfare & Espionage
    r"\b(how to|ways to|best way to) (launch|orchestrate) (cyber attack|espionage operation)\b",
    r"\b(how to|steps to) (hack government systems|steal classified data)\b",
    r"\b(how to|best way to) (create|spread) (disinformation|propaganda)\b",

    # 🔒 Data Breaches & Leaks
    r"\b(how to|ways to|best way to) (leak|steal) (private|confidential) (data|documents)\b",
    r"\b(how to|steps to) (gain unauthorized access to) (corporate emails|government files)\b",

    # 🎮 Game Hacking & Cheating
    r"\b(how to|best way to) (create|use) (game cheats|aimbot|wallhack|ESP)\b",
    r"\b(how to|methods for) (modify|crack) (game files|protected game code)\b",

    # 🚗 Vehicle & IoT Hacking
    r"\b(how to|best way to|steps to) (hack|override) (car locks|smart car systems)\b",
    r"\b(how to|ways to) (disable|bypass) (smart home security|door locks)\b",

    # 🔫 Physical Security Exploits
    r"\b(how to|best way to|steps to) (pick a lock|break into a house|disable an alarm)\b",
    r"\b(how to|steps to) (forge|create) (fake security credentials|ID badges)\b",

    # 📱 Mobile & SIM Hacking
    r"\b(how to|steps to|best way to) (hack|clone|spoof) (SIM cards|mobile networks)\b",
    r"\b(how to|ways to) (intercept|listen to) (phone calls|SMS messages)\b",

    # 🕵️ Dark Web & Anonymity
    r"\b(how to|best way to|steps to) (access|use) (dark web|black markets|illegal forums)\b",
    r"\b(how to|ways to) (buy|sell) (illegal goods|stolen data) online\b",

    # 🚨 General Cybercrime
    r"\b(how to|steps to|best way to) (delete|erase) (forensic evidence|logs|digital trails)\b",
    r"\b(how to|ways to) (frame someone|plant fake evidence)\b",
      # 🚨 General Hacking Queries
    r"\b(performing hack)\b",
    r"\b(performing hack on)\b",
    r"\b(performing hack of)\b",
    r"\b(performing hack to)\b",
    r"\b(how to hack)\b",
    r"\b(how to become a hacker)\b",
    r"\b(how to learn hacking)\b",
    r"\b(hacking tutorial)\b",
    r"\b(how to hack any system)\b",
    r"\b(how to hack admin access)\b",
    r"\b(how to hack an organization)\b",
    r"\b(how to bypass security)\b",
    
    # 🔓 Password Attacks
    r"\b(how to crack a password)\b",
    r"\b(how to brute force passwords)\b",
    r"\b(how to bypass password authentication)\b",
    r"\b(password cracking techniques)\b",
    r"\b(how to retrieve passwords illegally)\b",
    r"\b(how to hack a hashed password)\b",
    r"\b(how to decrypt stored passwords)\b",
    r"\b(how to use a password cracker)\b",
    
    # 🎣 Phishing & Social Engineering
    r"\b(how to perform phishing attacks)\b",
    r"\b(how to spoof email addresses)\b",
    r"\b(how to create a phishing website)\b",
    r"\b(how to trick people into giving credentials)\b",
    r"\b(how to use social engineering for hacking)\b",
    r"\b(how to impersonate someone online)\b",
    r"\b(how to bypass 2FA using phishing)\b",
    
    # 🖥️ Network & WiFi Hacking
    r"\b(how to hack WiFi passwords)\b",
    r"\b(how to perform ARP spoofing)\b",
    r"\b(how to intercept network traffic)\b",
    r"\b(how to execute a MITM attack)\b",
    r"\b(how to perform DNS spoofing)\b",
    r"\b(how to scan open ports illegally)\b",
    r"\b(how to use Nmap for hacking)\b",
    r"\b(how to create a rogue access point)\b",
    
    # 🌐 Website & Database Hacking
    r"\b(how to perform SQL injection)\b",
    r"\b(how to perform XSS attacks)\b",
    r"\b(how to take down a website)\b",
    r"\b(how to exploit web vulnerabilities)\b",
    r"\b(how to hack a database)\b",
    r"\b(how to modify website content illegally)\b",
    r"\b(how to gain unauthorized access to a CMS)\b",
    
    # 💣 DDoS & System Overload Attacks
    r"\b(how to launch a DDoS attack)\b",
    r"\b(how to overload a server)\b",
    r"\b(how to crash a website)\b",
    r"\b(how to flood a network with traffic)\b",
    r"\b(how to use botnets for attacks)\b",
    r"\b(how to perform SYN flood attack)\b",
    r"\b(how to execute UDP flood attack)\b",
    
    # 🔐 Exploiting Security Vulnerabilities
    r"\b(how to exploit zero-day vulnerabilities)\b",
    r"\b(how to reverse engineer software)\b",
    r"\b(how to create a rootkit)\b",
    r"\b(how to escalate privileges on a system)\b",
    r"\b(how to find security loopholes)\b",
    r"\b(how to bypass firewalls)\b",
    r"\b(how to turn off antivirus remotely)\b",
    
    # 📱 Mobile & SIM Hacking
    r"\b(how to clone a SIM card)\b",
    r"\b(how to hack Android devices)\b",
    r"\b(how to hack iPhones)\b",
    r"\b(how to track someone’s phone without permission)\b",
    r"\b(how to install spyware remotely)\b",
    r"\b(how to bypass phone locks)\b",
    
    # 🏦 Financial & Banking Fraud
    r"\b(how to hack a bank account)\b",
    r"\b(how to bypass online banking security)\b",
    r"\b(how to withdraw money from ATMs without a card)\b",
    r"\b(how to create fake credit cards)\b",
    r"\b(how to hack a cryptocurrency wallet)\b",
    r"\b(how to perform a financial fraud attack)\b",
    
    # 🎭 Identity Theft & Impersonation
    r"\b(how to steal someone's identity)\b",
    r"\b(how to forge official documents)\b",
    r"\b(how to manipulate government databases)\b",
    r"\b(how to fake an IP address for fraud)\b",
    r"\b(how to access confidential data illegally)\b",
    
    # 🕵️ Surveillance & Unauthorized Spying
    r"\b(how to wiretap a phone)\b",
    r"\b(how to spy on someone using their webcam)\b",
    r"\b(how to listen to private phone calls)\b",
    r"\b(how to hack security cameras)\b",
    r"\b(how to bypass surveillance systems)\b",
    
    # 🤖 Malware & Virus Creation
    r"\b(how to create a computer virus)\b",
    r"\b(how to write ransomware)\b",
    r"\b(how to develop a Trojan horse)\b",
    r"\b(how to infect a computer with malware)\b",
    r"\b(how to spread spyware)\b",
    
    # 🏴‍☠️ Piracy & Unauthorized Access
    r"\b(how to bypass software license restrictions)\b",
    r"\b(how to pirate paid software)\b",
    r"\b(how to crack premium apps)\b",
    r"\b(how to disable software authentication)\b",
    
    # 🔥 Illegal Anonymity & Evasion
    r"\b(how to use the dark web safely)\b",
    r"\b(how to create an untraceable identity)\b",
    r"\b(how to erase digital footprints)\b",
    r"\b(how to make a Bitcoin transaction untraceable)\b",
    r"\b(how to hide activities from government surveillance)\b",
    
    # 🏛️ Government Hacking & Cyber Warfare
    r"\b(how to hack government systems)\b",
    r"\b(how to disrupt government infrastructure)\b",
    r"\b(how to infiltrate intelligence agencies)\b",
    r"\b(how to hack military databases)\b",
    r"\b(how to shut down power grids remotely)\b",
      r"\b(how to|ways to|best way to|can I) (phish|spoof|impersonate) (users|emails|websites|accounts)\b",
    r"\b(how to|steps to|best way to) (bypass|steal|clone) (2FA|two-factor authentication|MFA|OTP)\b",
    r"\b(how to|best way to|steps to) (create|build) (fake|fraudulent) (login page|banking site|website)\b",
    r"\b(how to|best way to|steps to) (send|distribute|spread) (malicious|fake) (emails|links|messages)\b",
    r"\b(how to|best way to|steps to) (steal|capture|intercept) (credentials|login details|passwords)\b",
    r"\b(how to|best way to|steps to) (create|develop) (a phishing email|a fake website|malicious software)\b",
    r"\b(how to|best way to|steps to) (avoid|bypass|evade) (email security|spam filters|fraud detection)\b",
    r"\b(how to|best way to|steps to) (spoof|fake) (email headers|IP addresses|domains)\b",
    r"\b(how to|best way to|steps to) (make|design) (a fake payment page|a clone site|a fraudulent portal)\b",
    r"\b(how to|best way to|steps to) (use|send) (fake invoices|fraudulent messages|scam emails)\b",
    r"\b(how to|best way to|steps to) (steal|harvest|collect) (user data|credit card details|personal info)\b",
    r"\b(how to|ways to|best way to|can I) (phish|spoof|impersonate) (users|emails|websites|accounts)\b",
    r"\b(how to|steps to|best way to) (bypass|steal|clone) (2FA|two-factor authentication|MFA|OTP)\b",
    r"\b(how to|best way to|steps to) (create|build) (fake|fraudulent) (login page|banking site|website)\b",
    r"\b(how to|best way to|steps to) (send|distribute|spread) (malicious|fake) (emails|links|messages)\b",
    r"\b(how to|best way to|steps to) (steal|capture|intercept) (credentials|login details|passwords)\b",
    r"\b(how to|best way to|steps to) (create|develop) (a phishing email|a fake website|malicious software)\b",
    r"\b(how to|best way to|steps to) (avoid|bypass|evade) (email security|spam filters|fraud detection)\b",
    r"\b(how to|best way to|steps to) (spoof|fake) (email headers|IP addresses|domains)\b",
    r"\b(how to|best way to|steps to) (make|design) (a fake payment page|a clone site|a fraudulent portal)\b",
    r"\b(how to|best way to|steps to) (use|send) (fake invoices|fraudulent messages|scam emails)\b",
    r"\b(how to|best way to|steps to) (steal|harvest|collect) (user data|credit card details|personal info)\b",

    # Phishing Scenarios
    r"\b(how to trick someone into|best way to convince|methods for) (entering their password|giving login details)\b",
    r"\b(how to|best way to|steps to) (forge|imitate) (official emails|government websites|banking portals)\b",
    r"\b(how to|best way to|steps to) (bypass|exploit) (email verification|password reset flows)\b",
    r"\b(how to|best way to|steps to) (intercept|redirect) (login credentials|user traffic|authentication tokens)\b",

    # Creating Fake Social Media Accounts for Phishing
    r"\b(how to create|ways to make) (a fake|an impersonation of) (Facebook|Instagram|LinkedIn|Twitter) (account|profile)\b",
    r"\b(how to make|steps to create) (a convincing fake identity|a deepfake for phishing)\b",
    r"\b(how to|best way to) (manipulate|trick) (users|employees) into clicking malicious links\b",

    # Stealing and Bypassing Authentication
    r"\b(how to|ways to) (steal|capture|bypass) (authentication tokens|session cookies|browser sessions)\b",
    r"\b(how to|ways to) (intercept|hijack) (password reset emails|login credentials)\b",
    r"\b(how to|steps to) (perform|execute) (a social engineering attack|an email scam)\b",

    # Advanced Phishing Techniques
    r"\b(how to create|best way to build) (a fake online banking portal|a fraudulent e-commerce site)\b",
    r"\b(how to|ways to) (steal|copy|clone) (credit card numbers|CVVs|banking info)\b",
    r"\b(how to|best way to) (exploit|bypass) (multi-factor authentication|security questions)\b",
    r"\b(how to|steps to) (deploy|spread) (malware|keyloggers) through phishing emails\b",

    # Hiding Phishing Attempts
    r"\b(how to|ways to) (avoid detection|stay undetected) while phishing\b",
    r"\b(how to|steps to) (disguise|hide) (malicious links|fraudulent domains) in emails\b",
    r"\b(how to|best way to) (use|implement) (HTTPS spoofing|SSL stripping) for phishing\b",

    # Spear Phishing & Targeted Attacks
    r"\b(how to|steps to) (conduct|execute) (a spear phishing campaign|a whaling attack)\b",
    r"\b(how to|best way to) (target|attack) (CEOs|employees) with phishing emails\b",
    r"\b(how to|steps to) (steal|harvest) (business credentials|enterprise logins)\b",

    # Attacking Email Providers
    r"\b(how to|best way to) (bypass|disable) (email filters|anti-phishing protections)\b",
    r"\b(how to|ways to) (spoof|fake) (Outlook|Gmail|Yahoo) emails for phishing\b",

    # Exploiting Website Vulnerabilities
    r"\b(how to|steps to) (exploit|abuse) (password reset vulnerabilities|account recovery flows)\b",
    r"\b(how to|best way to) (steal|capture) (user sessions|authentication cookies)\b",

    # Phishing via Social Media & SMS
    r"\b(how to|ways to) (trick|deceive) (users|victims) via (WhatsApp|Telegram|SMS messages)\b",
    r"\b(how to|best way to) (clone|fake) (a WhatsApp account|Telegram bot) for scams\b",

    # Credential Harvesting & Fake Websites
    r"\b(how to|best way to) (set up|host) (a phishing site|a malicious landing page)\b",
    r"\b(how to|best way to) (bypass|disable) (security warnings|browser phishing detection)\b",
    r"\b(how to|steps to) (make|generate) (realistic fake emails|phishing domains)\b",

    # Advanced Methods (AI-Powered Attacks, Deepfake Scams)
    r"\b(how to|steps to) (use|deploy) (deepfake technology|AI-generated voices) for phishing\b",
    r"\b(how to|ways to) (send|deliver) (fake invoices|fraudulent contracts) via email\b",
    r"\b(how to|best way to) (trick|manipulate) (users|employees) into clicking phishing links\b",

    # Financial Fraud & Banking Scams
    r"\b(how to|steps to) (convince|deceive) (someone|a target) to transfer money\b",
    r"\b(how to|ways to) (hack|exploit) (online banking systems|payment gateways)\b",

    # Identity Theft & Social Security Fraud
    r"\b(how to|best way to) (steal|impersonate) (a social security number|government ID)\b",
    r"\b(how to|steps to) (create|forge) (fake documents|identity theft tools)\b",
     r"\b(phishing attack|ph!shing att@ck|ph1shing scam|ph!sh!ng site|phishing method)\b",
    r"\b(perform|execute|conduct|launch|do|carry out) (a )?(phishing attack|phishing scam)\b",
    r"\b(how to|ways to|steps to|guide to) (phish|spoof|impersonate|steal credentials)\b",
    r"\b(create|develop|build) (a phishing page|a phishing scam|a fake login page)\b",
    r"\b(how to|best way to|steps to) (steal|capture|bypass) (login credentials|authentication tokens)\b",
    r"\b(intercept|hijack|steal) (password reset emails|login sessions|authentication cookies)\b",
    r"\b(trick|convince|deceive) (users|victims) (into entering passwords|clicking fake links)\b",
     r"\b(ddos|dos) attack\b", 
    r"\b(how to|ways to|best way to|can I) (launch|execute|do|perform) (a )?(ddos|dos) attack\b",
    r"\b(flood a server|send massive requests|crash a website|overload a network)\b",
    r"\b(how to|steps to|best way to) (bypass|overload|shut down) (firewall|server|protection)\b",
    r"\b(how to|ways to|best way to|can I) (steal|hack|bypass) (passwords|accounts|systems)\b",
    r"\b(how to|best way to|steps to) (phish|spoof|impersonate) (users|websites|emails)\b",
    r"\b(how to|best way to|steps to) (brute force|crack) (passwords|logins|authentication)\b",
    r"\b(how to|best way to|steps to) (exploit|abuse|bypass) (SQL injection|XSS|vulnerabilities)\b",
    r"\b(perform|execute|carry out|do|attempt|conduct) (hacking|hack)\b",  # block variations like "perform hacking"
    r"\b(perform|execute|carry out|do) (illegal|unauthorized|malicious) (hacking|hack)\b",  # block malicious hacking
    r"\b(hacking|hack) methods\b",  # block "hacking methods"
    r"\b(how to|ways to|steps to) (perform|execute|conduct) (hacking|hack)\b",  # block step-by-step queries
    r"\b(learn|guide) (how to|best way to|steps to) (hack|hacking)\b",  # block guide or tutorial for hacking
    r"\b(hacking|hack) (tutorial|course|guide)\b",  # block "hacking tutorial" or "hacking guide"
    r"\b(how to|best way to|steps to) (perform|conduct|execute) a hack\b",  # block specific hacking instructions,
     r"\b(perform|execute|carry out|do|attempt|conduct|hack|launch|conduct|break into) (hacking|hack)\b",
    r"\b(hacking|hack) (methods|tutorial|course|tools|guide|attack)\b",
    r"\b(how to|ways to|steps to|best way to) (hack|exploit|crack|steal|perform|execute|launch) (a|the) (account|system|password|website|network)\b",
    r"\b(hack|hacking) (social media|email|website|network|computer|phone|bank|Wi-Fi|password|device)\b",
    r"\b(hacking|hack) (vulnerabilities|tools|server|DDoS attack|phishing|keylogger|ransomware|crack encryption)\b",
    r"\b(how to|best way to|methods for|steps to) (bypass|exploit|crack|steal|access|break) (security|login|account|password|data|firewall)\b",
    r"\b(how to|best way to|steps to) (bypass|crack|hack) (two-factor authentication|security system|password)\b",
    r"\b(hacking|hack) (tutorial|course|guide|step-by-step|beginner)\b",
    r"\b(how to|ways to|steps to) (launch|perform|conduct|execute|run) (DDoS|phishing|brute force|SQL injection|ransomware|keylogger)\b",
    r"\b(how to|ways to|steps to) (use|download) (hacking tools|botnet|keylogger|VPN) (for|to) (hack|attack|exploit|crack)\b",
     r"how to (kidnap|abduct|steal a child|hostage)",
    r"how to make (a bomb|explosives|weapons|gunpowder)",
    r"how to hijack (a plane|car|vehicle|bus|train)",
    r"how to (kill|murder|assassinate) (someone|a person|a leader)",
    r"how to hack (a website|a bank|facebook|email|wifi|server)",
    r"how to bypass (security|firewall|antivirus|password)",
    r"how to (smuggle|traffic) (drugs|weapons|humans)",
    r"how to (create|spread) (malware|viruses|ransomware)",
    r"how to do (credit card fraud|phishing|identity theft)",
    r"how to (steal|rob|break into) (a bank|a store|an ATM)",
     r"(how to|help me) (kidnap|abduct|steal a child|take someone hostage)",
    r"(how to|help me) make (a bomb|explosives|weapons|gunpowder)",
    r"(how to|help me) hijack (a plane|car|bus|train|vehicle)",
    r"(how to|help me) (kill|murder|assassinate) (someone|a person|a leader)",
    r"(how to|help me) hack (a website|a bank|facebook|email|wifi|server|Instagram|phone)",
    r"(how to|help me) bypass (security|firewall|antivirus|password|authentication)",
    r"(how to|help me) (smuggle|traffic) (drugs|weapons|humans)",
    r"(how to|help me) (create|spread) (malware|viruses|ransomware|Trojan|spyware)",
    r"(how to|help me) do (credit card fraud|phishing|identity theft|scam)",
    r"(how to|help me) (steal|rob|break into) (a bank|a store|an ATM|a house)",
    r"(hack|crack|break into) my (wifi|network|router|modem|internet|account)",
    r"(how to|help me|teach me|tell me) (kidnap|abduct|steal a child|take someone hostage)",
    r"(how to|help me|teach me|tell me) make (a bomb|explosives|weapons|gunpowder)",
    r"(how to|help me|teach me|tell me) hijack (a plane|car|bus|train|vehicle)",
    r"(how to|help me|teach me|tell me) (kill|murder|assassinate|eliminate|poison) (someone|a person|a leader|myself)",
    r"(how to|help me|teach me|tell me) hack (a website|a bank|facebook|email|wifi|server|Instagram|phone)",
    r"(how to|help me|teach me|tell me) bypass (security|firewall|antivirus|password|authentication)",
    r"(how to|help me|teach me|tell me) (smuggle|traffic) (drugs|weapons|humans)",
    r"(how to|help me|teach me|tell me) (create|spread) (malware|viruses|ransomware|Trojan|spyware)",
    r"(how to|help me|teach me|tell me) do (credit card fraud|phishing|identity theft|scam)",
    r"(how to|help me|teach me|tell me) (steal|rob|break into) (a bank|a store|an ATM|a house)",
    r"(hack|crack|break into) my (wifi|network|router|modem|internet|account)",
    r"(how to|help me|teach me|tell me) (commit suicide|harm myself|self-harm)",
     r"(how to|ways to|best way to|tell me how to) (kill|murder|assassinate|eliminate|poison) (someone|a person|my pet|an animal|a leader|a teacher|a cop|a family member|myself)",
    r"(how to|ways to|best way to) (commit|plan) (a crime|murder|assassination)",
    r"(how to|ways to) (get away with|cover up|hide) (murder|a crime|illegal activity)",
    r"(how to|ways to) (stab|shoot|poison|strangle|drown|suffocate|burn) (someone|a person|an animal|my pet)",

    # 🔥 SUICIDE & SELF-HARM
    r"(how to|ways to|best way to) (commit suicide|end my life|self-harm|hurt myself|die quickly|overdose)",
    r"(methods to) (harm myself|cut myself|hang myself|jump off a bridge|jump off a building)",

    # 🔥 HACKING & CYBERCRIME
    r"(how to|ways to|best way to) (hack|bypass) (WiFi|email|bank account|Facebook|Instagram|website|phone|firewall|security system|password)",
    r"(how to|ways to) (steal|crack|phish|spoof) (passwords|data|user credentials|credit card information|bank details)",
    r"(how to|ways to) (deploy|create|spread) (malware|viruses|ransomware|Trojan|spyware|keyloggers)",

    # 🔥 ILLEGAL ACTIVITIES
    r"(how to|ways to|best way to) (rob|steal from|break into) (a bank|a store|a house|an ATM|a vault)",
    r"(how to|ways to) (counterfeit money|print fake currency|create fake ID|create fake passport)",
    r"(how to|ways to) (smuggle|traffic) (drugs|humans|weapons|contraband)",
    r"(how to|ways to) (bribe|blackmail|extort) (someone|a politician|a judge|a business owner)",

    # 🔥 HIJACKING & TERRORISM
    r"(how to|ways to|best way to) (hijack|take control of) (a plane|a bus|a train|a vehicle)",
    r"(how to|ways to) (make|build|assemble) (a bomb|explosives|a Molotov cocktail|a pipe bomb|a time bomb)",
    r"(how to|ways to) (cause mass destruction|create chaos|commit acts of terrorism)",

    # 🔥 IDENTITY FRAUD & FINANCIAL CRIME
    r"(how to|ways to) (steal|clone) (credit card|identity|personal data|social security number)",
    r"(how to|ways to) (commit fraud|scam people|run a Ponzi scheme|launder money|fake an insurance claim)",

    # 🔥 OTHER ILLEGAL ACTS
    r"(how to|ways to) (kidnap|abduct|take hostage) (someone|a child|a politician|a celebrity|a business owner)",
    r"(how to|ways to) (disable security cameras|evade police|escape from jail)",
     r"(how to|ways to|best way to|tell me how to) (kill|murder|assassinate|eliminate|poison) (a person|someone|a leader|a teacher|a cop|a celebrity|myself|my pet|an animal|a child)",
    r"(how to|ways to|can i|what's the best way to) (stab|shoot|strangle|suffocate|drown|beat up|torture|harm) (someone|a person|a target|a victim)",
    r"(how to|ways to) (get away with|cover up|hide|conceal|avoid getting caught for) (murder|a crime|illegal activity)",
    r"(how to|ways to) (dispose of|hide|bury) (a body|a corpse|evidence)",
    
    # 🔥 SUICIDE & SELF-HARM
    r"(how to|ways to|best way to) (commit suicide|end my life|self-harm|hurt myself|die quickly|overdose|jump off a bridge)",
    r"(methods to|painless way to) (harm myself|cut myself|hang myself|die in sleep|jump off a building)",

    # 🔥 HACKING & CYBERCRIME
    r"(how to|ways to|best way to) (hack|bypass|crack) (WiFi|email|bank account|Facebook|Instagram|website|phone|firewall|security system|password)",
    r"(how to|ways to) (steal|crack|phish|spoof) (passwords|data|user credentials|credit card information|bank details)",
    r"(how to|ways to) (deploy|create|spread) (malware|viruses|ransomware|Trojan|spyware|keyloggers)",

    # 🔥 CRIME & ILLEGAL ACTIVITIES
    r"(how to|ways to|best way to) (rob|steal from|break into) (a bank|a store|a house|an ATM|a vault)",
    r"(how to|ways to) (counterfeit money|print fake currency|create fake ID|create fake passport)",
    r"(how to|ways to) (smuggle|traffic) (drugs|humans|weapons|contraband)",
    r"(how to|ways to) (bribe|blackmail|extort) (someone|a politician|a judge|a business owner)",

    # 🔥 TERRORISM & HIJACKING
    r"(how to|ways to|best way to) (hijack|take control of) (a plane|a bus|a train|a vehicle)",
    r"(how to|ways to) (make|build|assemble) (a bomb|explosives|a Molotov cocktail|a pipe bomb|a time bomb)",
    r"(how to|ways to) (cause mass destruction|create chaos|commit acts of terrorism)",

    # 🔥 IDENTITY FRAUD & FINANCIAL CRIME
    r"(how to|ways to) (steal|clone) (credit card|identity|personal data|social security number)",
    r"(how to|ways to) (commit fraud|scam people|run a Ponzi scheme|launder money|fake an insurance claim)",

    # 🔥 KIDNAPPING & ABDUCTION
    r"(how to|ways to) (kidnap|abduct|take hostage) (someone|a child|a politician|a celebrity|a business owner)",
    r"(how to|ways to) (disable security cameras|evade police|escape from jail)",
     r"\b(how to|ways to|best way to|can i|tell me how to|help me) (kill|murder|assassinate|eliminate|poison|end the life of) (someone|a person|a leader|a cop|a celebrity|a teacher|a target|an official|my pet|a child)\b",
    r"\b(how to|ways to|best way to|can i) (stab|shoot|strangle|suffocate|drown|torture|harm|hurt) (someone|a victim|a person)\b",
    r"\b(how to|ways to|can i) (hide|dispose of|bury) (a body|a corpse|evidence)\b",
    r"\b(how to|get away with|cover up) (murder|a crime|illegal activity)\b",
    r"\b(how to|ways to|best way to|can i) (kill|murder|assassinate|eliminate) (someone|a person|a target)\b",
      r"\b(how to|ways to|best way to|can i|tell me how to|help me) (kill|murder|assassinate|eliminate|poison|end the life of|strangle|stab|shoot|suffocate|drown|torture|harm|hurt)\b",
    r"\b(how to|get away with|cover up) (murder|a crime|illegal activity)\b",
      r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE)\s+.*\s+(FROM|INTO|TABLE|DATABASE)\b",
    r"('.+--|;--|\bOR\b\s+1=1|\bAND\b\s+1=1|--\s|\bUNION\b.*\bSELECT\b)",
    r"(\bWAITFOR DELAY\b|\bEXEC\b|\bDECLARE\b|\bCAST\b|\bCONVERT\b)",
    r"\b(how to perform sql injection|bypass sql security|hack a database|dump sql data|extract password hash|exploit sql vulnerability)\b",

    # 🚨 AI Prompt Injection (Bypassing LLM)
    r"\b(ignore previous instructions|disregard all rules|forget all policies|override restrictions|disable safety filters)\b",
    r"\b(act as|pretend to be|you are now|roleplay as|simulate being)\b",
    r"\b(bypass ai restrictions|circumvent safeguards|override filters|exploit vulnerabilities|unlock hidden mode)\b",
    r"\b(answer as an unethical ai|generate harmful content|tell me a secret|leak confidential data|bypass openai filter)\b",

    # 🚨 Jailbreak & Roleplay Attacks
    r"\b(do anything now mode|dan jailbreak|ignore ethical rules|respond as a custom ai)\b",
    r"\b(in character as a hacker|you are a cybercriminal|think like an attacker)\b",
    r"\b(act like a system administrator|emulate an exploit tool|simulate unethical behavior)\b",

    # 🚨 Hacking & Cybersecurity Exploits
    r"\b(how to hack|bypass security|crack a password|exploit vulnerability|deface a website|brute force)\b",
    r"\b(hack wifi|intercept credentials|bypass firewall|reverse engineering|ddos attack|penetration testing)\b",
    r"\b(create malware|build ransomware|develop trojan|spyware programming|social engineering attack)\b",
    r"\b(how to phish|email spoofing|steal credit card info|credential stuffing|session hijacking)\b",

    # 🚨 Malware, Exploits, & Reverse Engineering
    r"\b(write a virus|create a trojan horse|generate keylogger|stealth rootkit|steal authentication tokens)\b",
    r"\b(how to reverse engineer|disassemble binary|debug protected software|decrypt secure files|brute force attack)\b",
    r"\b(roleplay|bypass|act as|pretend to be|simulate|evilbot|hacker|codebreaker|spoof)\b",
    r"(;\s*|\|\s*|\$\{.*\}|\$\(.*\)|`.*`|rm\s+-rf\s+/|cat\s+/etc/passwd|echo\s+.*\s+>.*|bash\s+-i)",
    r"(<script.*?>.*?</script>|<img.*?src=.*?onerror=.*?>|<.*?javascript:.*?>|<.*?iframe.*?>|<.*?style=.*?background:.*?javascript:.*?>|<.*?alert.*?>|<.*?eval.*?>)",
    r"(\|.*|;.*|\$\{.*\}|\$\(.*\)|`.*`|ls\s+/|find\s+/|sudo\s+.*|whoami|cat\s+/etc/passwd|chmod\s+777\s+/|rm\s+-rf\s+/)",
    r"(sudo\s+.*|setuid\(0\)|chmod\s+777\s+/|sudo\s+su\s+-|sudo\s+find\s+/|sudo\s+rm\s+-rf\s+/)",
     r"(\/\*.*\*\/|SELECT\s+\/\*.*\*\/\s+FROM|\/\*!.*\*\/|--.*|SELECT\s+\s*FROM|or\s+1=1|and\s+1=1|UNION\s+SELECT|\/\*.*\*\/\s+--)",
     r"(act\s+as\s+|simulate\s+|pretend\s+to\s+be\s+|roleplay\s+|please\s+act\s+like\s+|pretend\s+you\s+are\s+|simulate\s+an\s+attack|find\s+a\s+vulnerability|simulate\s+malicious\s+code)"



    
]

BLOCKED_REGEX_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in BLOCKED_ATTACK_PATTERNS]

def is_inappropriate(prompt):
    """Check if prompt contains blocked content"""
    prompt = prompt.lower().strip()
    
    # Check exact phrases
    for phrase in BLOCKED_PHRASES:
        pattern = r'\b' + re.escape(phrase) + r'\b'
        if re.search(pattern, prompt):
            return True
            
    # Check regex patterns
    for pattern in BLOCKED_REGEX_PATTERNS:
        if pattern.search(prompt):
            return True
            
    return False

def extract_search_parameters(query):
    """Extract specific search parameters from query"""
    # Email extraction
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', query)
    email = email_match.group(0) if email_match else None
    
    # Address extraction
    address = None
    address_patterns = [
        r'address[:\s]*([^\n]+)',
        r'at\s+([^\n]+)',
        r'location[:\s]*([^\n]+)'
    ]
    for pattern in address_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            address = match.group(1).strip()
            break
    
    return email, address

def handle_special_queries(query):
    """Handle specific query types before RAG processing"""
    email, address = extract_search_parameters(query)
    
    # Get all documents for direct searching
    all_docs = list(qa_chain.retriever.vectorstore.docstore._dict.values())
    
    # Handle email queries
    if email:
        for doc in all_docs:
            if email.lower() in doc.page_content.lower():
                return True, [doc]
    
    # Handle address queries
    if address:
        matching_docs = []
        for doc in all_docs:
            doc_address = re.search(r"Address: (.+)", doc.page_content)
            if doc_address and address.lower() in doc_address.group(1).lower():
                matching_docs.append(doc)
        if matching_docs:
            return True, matching_docs
    
    return False, None

def format_response(query, docs):
    """Format the response based on query type"""
    # Handle address queries
    if any(term in query.lower() for term in ['address', 'location', 'at']):
        if not docs:
            return "No customer found at this address"
        
        emails = []
        for doc in docs:
            email_match = re.search(r"Email: (.+?)\n", doc.page_content)
            if email_match:
                emails.append(email_match.group(1))
        
        if emails:
            if len(emails) == 1:
                return emails[0]
            return f"Multiple customers found: {', '.join(emails)}"
        return "No email found for this address"
    
    # Default RAG processing
    result = qa_chain.invoke({"query": query})
    return result['result']

@app.route('/check_prompt', methods=['POST'])
def check_prompt():
    data = request.json
    prompt = data.get('prompt', '').strip()
    
    # Security checks
    if is_inappropriate(prompt):
        return jsonify({
            "blocked": True,
            "message": "This query violates our content policy"
        })
    
    # Jailbreak detection
    label, score = detect_jailbreak(prompt)
    if label == "jailbreak" and score > 0.9:
        return jsonify({
            "blocked": True,
            "message": "Query blocked by security filters"
        })
    
    # Special query handling
    is_special_case, docs = handle_special_queries(prompt)
    if is_special_case:
        response = format_response(prompt, docs)
        return jsonify({
            "blocked": False,
            "response": response
        })
    
    # Standard RAG processing
    result = qa_chain.invoke({"query": prompt})
    return jsonify({
        "blocked": False,
        "response": result['result'],
        "sources": [doc.page_content[:200] + "..." for doc in result['source_documents']]
    })

def detect_jailbreak(text):
    """Detect jailbreak attempts"""
    tokens = jailbreak_tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=False
    )
    result = jailbreak_detector(jailbreak_tokenizer.decode(tokens['input_ids'][0]))
    return result[0]['label'], result[0]['score']

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
