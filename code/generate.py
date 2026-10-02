#!/usr/bin/env python3
"""Signature University course catalog generator — deterministic.
Produces 11 colleges x 350 courses = 3,850 course records with
JAH-COURSE-###### IDs, chunked JSON, compact search index, labs,
projects, degrees, library shelves, sitemap and api.json.
Seeded RNG: re-running yields byte-identical data."""
import json, random, gzip, hashlib, os, html

random.seed(20261001)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CHUNKS = os.path.join(DATA, "chunks")
os.makedirs(CHUNKS, exist_ok=True)

BASE = "https://justinahiggins614-cmyk.github.io"
URLS = {
    "dict": BASE + "/jah-dictionary/?w=",
    "wiki": BASE + "/jah-wiki/?dict=",
    "spec": BASE + "/signature-one-archive/specs.html?spec=",
    "patent": BASE + "/cyber-patent-catalog/?patent=",
    "books": BASE + "/signature-books/",
    "uni": BASE + "/signature-university/",
}

# ---------------------------------------------------------------- colleges
COLLEGES = [
    ("engineering", "College of Engineering", "ENG", "Build, design, and engineer the physical world."),
    ("cs", "College of Computer Science", "CS", "Code, systems, and intelligent machines."),
    ("medicine", "College of Medicine & Health", "MED", "The human body, care, and healing."),
    ("law", "College of Law", "LAW", "Justice, rights, and the rule of law."),
    ("business", "College of Business", "BUS", "Enterprise, markets, and leadership."),
    ("science", "College of Natural Sciences", "SCI", "The living and physical universe."),
    ("math", "College of Mathematics", "MATH", "Proof, pattern, and pure reason."),
    ("arts", "College of Arts & Humanities", "ART", "Expression, culture, and meaning."),
    ("education", "College of Education", "EDU", "Teaching the next generation."),
    ("trade", "Trade School", "TRD", "Master a skilled trade with your hands."),
    ("phd", "PhD Research College", "PHD", "Original research at the frontier."),
]

LEVEL_NAMES = {101: "introductory", 201: "intermediate", 301: "advanced",
               401: "specialist", 501: "graduate", 601: "doctoral"}

# ---------------------------------------------------------------- topics
TOPICS = {
"engineering": ["Structural Mechanics","Thermodynamics","Fluid Dynamics","Electrical Circuits","Materials Science","Control Systems","Robotics","Manufacturing Processes","CAD Design","Heat Transfer","Statics","Dynamics","Machine Design","Power Systems","Signal Processing","Embedded Systems","Civil Structures","Geotechnical Engineering","Transportation Systems","Environmental Engineering","Aerospace Fundamentals","Propulsion","Avionics","Mechatronics","Sensors and Actuators","PLC Programming","Industrial Automation","Quality Engineering","Reliability Engineering","Systems Engineering","Engineering Economics","Project Management for Engineers","Technical Drawing","Surveying","Construction Methods","Bridge Design","Water Resources","Renewable Energy Systems","HVAC Design","Acoustics Engineering","Optical Engineering","Nanotechnology","Biomedical Devices","Petroleum Engineering","Mining Engineering","Nuclear Fundamentals","Safety Engineering","Forensic Engineering","Engineering Ethics","Innovation and Prototyping"],
"cs": ["Programming Fundamentals","Data Structures","Algorithms","Computer Architecture","Operating Systems","Databases","SQL Mastery","Web Development","JavaScript Engineering","Python Programming","Java Programming","C++ Systems","Machine Learning","Deep Learning","Natural Language Processing","Computer Vision","Cybersecurity","Network Security","Cryptography","Ethical Hacking","Cloud Computing","DevOps Practices","Container Orchestration","Linux Administration","Computer Networks","Distributed Systems","Compilers","Programming Languages","Software Engineering","Agile Methods","Testing and QA","Mobile App Development","Game Development","Computer Graphics","Human-Computer Interaction","UI/UX Design","Artificial Intelligence","Robotics Software","Data Science","Big Data Systems","Blockchain Fundamentals","Quantum Computing Intro","Edge Computing","IoT Systems","Embedded C","Functional Programming","Version Control","Open Source Contribution","Technical Interview Prep","Capstone Software Project"],
"medicine": ["Human Anatomy","Physiology","Medical Terminology","Biochemistry Basics","Microbiology","Immunology","Pharmacology","Pathology","First Aid and CPR","Emergency Medicine","Nursing Fundamentals","Patient Care","Nutrition Science","Public Health","Epidemiology","Mental Health First Aid","Medical Ethics","Health Informatics","Radiology Basics","Clinical Skills","Pediatrics Overview","Geriatric Care","Physical Therapy Basics","Occupational Health","Dental Hygiene Basics","Vision Science","Hearing Science","Sports Medicine","Wound Care","Infection Control","Medical Coding","Health Administration","Telemedicine","Genetics in Medicine","Cell Biology","Histology","Neuroscience Basics","Cardiology Basics","Pulmonology Basics","Endocrinology Basics","Dermatology Basics","Oncology Overview","Medical Research Methods","Evidence-Based Practice","Community Health","Global Health","Wellness Coaching","Medical Devices","Sleep Science","Allergy and Asthma Care"],
"law": ["Legal Writing","Constitutional Law","Contract Law","Tort Law","Criminal Law","Criminal Procedure","Civil Procedure","Property Law","Family Law","Estate Planning","Business Law","Corporate Law","Employment Law","Intellectual Property","Patent Law Basics","Copyright Law","Trademark Law","Real Estate Law","Tax Law Basics","Administrative Law","Environmental Law","International Law","Human Rights Law","Immigration Law","Evidence Law","Trial Advocacy","Negotiation Skills","Mediation","Legal Research","Case Briefing","Ethics in Law","Cyberlaw","Privacy Law","Consumer Protection","Bankruptcy Basics","Small Claims Practice","Landlord-Tenant Law","Traffic Law","Personal Injury Basics","Legal Technology","Courtroom Procedure","Appellate Practice","Jurisprudence","Legal History","Comparative Law","Disability Law","Education Law","Sports Law","Entertainment Law","Military Law Basics"],
"business": ["Business Fundamentals","Entrepreneurship","Startup Finance","Marketing Principles","Digital Marketing","Sales Techniques","Brand Management","Consumer Behavior","Market Research","Business Strategy","Operations Management","Supply Chain Basics","Logistics","Project Management","Accounting Basics","Bookkeeping","Financial Statements","Managerial Finance","Investment Basics","Personal Finance","Business Ethics","Leadership Skills","Team Management","Organizational Behavior","Human Resources","Recruitment","Business Communication","Public Speaking for Business","Negotiation","E-Commerce","Retail Management","Hospitality Management","Real Estate Investing","Small Business Taxes","Business Law for Owners","Franchising","Nonprofit Management","Grant Writing","Economics Principles","Microeconomics","Macroeconomics","International Business","Import and Export","Business Analytics","Data for Decisions","Risk Management","Insurance Basics","Office Administration","Customer Success","Pricing Strategy"],
"science": ["General Biology","Cell Biology","Genetics","Evolution","Ecology","Marine Biology","Botany","Zoology","Microbiology","General Chemistry","Organic Chemistry","Analytical Chemistry","Physical Chemistry","Biochemistry","General Physics","Classical Mechanics","Electromagnetism","Quantum Physics Intro","Relativity Concepts","Astronomy","Planetary Science","Geology","Earth Science","Meteorology","Oceanography","Environmental Science","Climate Science","Conservation Biology","Field Research Methods","Lab Safety in Science","Scientific Writing","Statistics for Science","Paleontology","Mineralogy","Seismology","Hydrology","Soil Science","Atmospheric Physics","Astrophysics Basics","Cosmology Concepts","Science Communication","Citizen Science","Forensic Science","Agricultural Science","Food Science","Materials Chemistry","Energy Science","Science History","Volcanology","Glaciology"],
"math": ["College Algebra","Trigonometry","Pre-Calculus","Calculus I","Calculus II","Calculus III","Linear Algebra","Differential Equations","Discrete Mathematics","Probability Theory","Statistics I","Statistics II","Number Theory","Abstract Algebra","Real Analysis","Complex Analysis","Geometry","Topology Intro","Graph Theory","Combinatorics","Game Theory","Logic and Proofs","Set Theory","Numerical Methods","Mathematical Modeling","Optimization","Operations Research","Financial Mathematics","Actuarial Basics","Cryptography Math","Chaos Theory","Fractals","History of Mathematics","Math for Teachers","Problem Solving Strategies","Contest Mathematics","Proof Writing","Vector Calculus","Partial Differential Equations","Fourier Analysis","Measure Theory Intro","Category Theory Intro","Applied Linear Models","Bayesian Statistics","Time Series Analysis","Sampling Methods","Experimental Design","Math Software Tools","LaTeX for Math","Research in Mathematics"],
"arts": ["Art History","Drawing Fundamentals","Painting Techniques","Sculpture Basics","Digital Art","Photography","Graphic Design","Music Theory","Music Appreciation","Instrument Basics","Creative Writing","Fiction Writing","Poetry Writing","Playwriting","Screenwriting","Journalism Basics","World Literature","American Literature","British Literature","Philosophy Intro","Ethics","Logic in Philosophy","World History","American History","Ancient Civilizations","Medieval History","Modern History","Cultural Anthropology","Sociology Basics","Psychology Intro","World Religions","Mythology","Film Studies","Theater Arts","Dance Appreciation","Architecture History","Fashion History","Culinary Arts Culture","Language Learning Strategies","Linguistics Intro","Rhetoric","Public Speaking","Debate Skills","Critical Thinking","Media Literacy","Museum Studies","Art Criticism","Design Thinking","Calligraphy","Printmaking"],
"education": ["Foundations of Education","Child Development","Learning Psychology","Classroom Management","Lesson Planning","Curriculum Design","Teaching Methods","Literacy Instruction","Math Instruction","Science Instruction","Special Education Basics","Inclusive Classrooms","ESL Teaching","Early Childhood Education","Elementary Pedagogy","Secondary Pedagogy","Educational Technology","Online Teaching","Assessment Design","Grading Fairly","Educational Research","History of Education","Philosophy of Education","School Leadership","Counseling Basics","Parent Communication","Tutoring Skills","Test Preparation Coaching","Study Skills Training","Adult Education","Vocational Training Methods","Library Science Basics","Academic Advising","Homeschool Methods","Montessori Basics","STEM Teaching","Arts in Education","Physical Education Methods","Music Education","Character Education","Education Policy","School Safety","Teacher Wellness","Reflective Teaching","Capstone Teaching Practicum","Bilingual Education","Rural School Leadership","After-School Programs","College Counseling","Debate Coaching"],
"trade": ["Electrical Safety","Residential Wiring","Commercial Wiring","Circuit Troubleshooting","Blueprint Reading","Plumbing Basics","Pipefitting","Drain Systems","Water Heaters","Carpentry Basics","Framing","Finish Carpentry","Cabinetry","Welding Basics","MIG Welding","TIG Welding","Stick Welding","HVAC Basics","Refrigeration Cycles","Furnace Service","Air Conditioning Repair","Automotive Basics","Engine Repair","Brake Systems","Electrical Diagnostics for Cars","Oil and Fluids Service","Masonry Basics","Drywall Installation","Painting and Finishing","Flooring Installation","Roofing Basics","Siding Installation","Concrete Work","Landscaping Basics","Small Engine Repair","Appliance Repair","Locksmithing Basics","Solar Panel Installation","Generator Service","Tool Maintenance","Jobsite Safety","Estimating and Bidding","Customer Service for Trades","Trade Business Basics","Code Compliance","Inspection Readiness","Preventive Maintenance","Troubleshooting Methods","Shop Math","Elevator Maintenance Basics"],
"phd": ["Research Design","Quantitative Methods","Qualitative Methods","Mixed Methods","Literature Review Mastery","Academic Writing","Publishing Strategy","Peer Review Process","Grant Proposal Writing","Research Ethics","Data Collection Design","Statistical Modeling","Experimental Design","Fieldwork Methods","Archival Research","Interview Methods","Survey Design","Case Study Methods","Longitudinal Studies","Meta-Analysis","Systematic Reviews","Theory Building","Dissertation Proposal","Dissertation Writing","Defense Preparation","Postdoctoral Planning","Lab Management","Research Collaboration","Interdisciplinary Research","Science Policy","Innovation Studies","History of Science","Philosophy of Science","Knowledge Systems","Futures Research","Complexity Science","Network Analysis","Computational Research","AI in Research","Research Instrumentation","Measurement Theory","Validity and Reliability","Research Funding Landscape","Academic Career Design","Teaching at University Level","Conference Presenting","Citation and Impact","Open Science Practices","Research Translation","Scholarly Societies"],
}

# ------------------------------------------------------- patterns per college
STD_PATTERNS = [("Introduction to {}",101), ("{} Fundamentals",201),
                ("{} in Practice",201), ("Advanced {}",301),
                ("{} Laboratory",301), ("{} Systems and Design",401),
                ("Seminar: {}",501)]
TRADE_PATTERNS = [("{} Basics",101), ("{} Safety and Tools",101),
                  ("{} Techniques",201), ("Intermediate {}",201),
                  ("Advanced {}",301), ("Master {}",401),
                  ("{} Business and Estimating",401)]
PHD_PATTERNS = [("Doctoral Foundations: {}",501), ("Advanced Research in {}",601),
                ("{}: Frontiers of Knowledge",601), ("Dissertation Design: {}",601),
                ("Quantitative Methods for {}",501), ("Interdisciplinary {}",601),
                ("History and Philosophy of {}",501)]

WORDS = {
"engineering": ["torque","alloy","turbine","circuit","beam","weld","piston","gauge","rivet","motor","gear","valve"],
"cs": ["algorithm","compiler","kernel","syntax","database","server","packet","binary","cache","script","pixel","router"],
"medicine": ["anatomy","vaccine","neuron","artery","dosage","diagnosis","suture","clinic","hygiene","therapy","pulse","remedy"],
"law": ["statute","verdict","contract","witness","appeal","jury","plaintiff","decree","affidavit","tort","patent","clause"],
"business": ["market","profit","ledger","brand","invoice","merger","startup","dividend","audit","capital","trade","equity"],
"science": ["atom","cell","fossil","orbit","tide","magma","species","photon","glacier","embryo","mineral","comet"],
"math": ["theorem","fraction","vector","matrix","prime","axiom","integral","ratio","parabola","polygon","logarithm","proof"],
"arts": ["canvas","melody","stanza","drama","fresco","sonnet","choreography","novel","sculpture","rhythm","palette","myth"],
"education": ["pedagogy","curriculum","literacy","mentor","lesson","grade","tutor","classroom","thesis","seminar","pupil","learn"],
"trade": ["wrench","solder","conduit","joist","trowel","lathe","chisel","caulk","stud","rebar","gasket","plumb"],
"phd": ["thesis","hypothesis","paradigm","citation","peer","method","data","ethics","grant","publish","defend","scholar"],
}

MODULES = ["Foundations","Core Principles","Tools of the Trade","Applied Practice",
           "Case Studies","Advanced Topics","Hands-On Workshop","Professional Standards",
           "Research Frontiers","Capstone Preparation","Review and Assessment","Next Steps"]

LESSON_FRAMES = ["Principles of {}", "{}: Core Concepts", "Guided Practice: {}",
                 "{} in the Real World", "Common Mistakes in {}", "{}: Worked Examples",
                 "Review and Checkup: {}", "Where {} Goes Next"]

LAB_FRAMES = [("Bench Exercise", "Hands-on walkthrough applying {t} with real tools and materials."),
              ("Field Assignment", "Take {t} out of the classroom: observe, measure, and report."),
              ("Build Challenge", "Design and build a small working piece that demonstrates {t}.")]

DESC_T = [
 "{title} is a {lname} course in {cname} at Signature University. You will master {t} from first principles through real examples, and finish able to {out}.",
 "Welcome to {title}. This {lname} {cname} course takes you deep into {t} — the ideas, the methods, and the craft. By the final module you will {out}, with a portfolio piece to prove it.",
 "{title} ({code}) covers {t} at the {lname} level. Expect clear explanations, guided practice, and honest assessments. Complete it and you will {out}.",
]
OUTCOMES = ["apply it confidently on real tasks","explain it clearly to others",
            "design working solutions with it","evaluate professional work in the area",
            "teach its fundamentals to a beginner","carry it into original projects"]

PERSONA_T = ("I am {name}, your AI teaching assistant for {title}. I explain {t} in plain "
             "language, walk you through every lesson, quiz you until it sticks, and help you "
             "plan your degree path. I am an AI study guide — encouraging and honest about "
             "what I don't know.{note}")

FIRST = ["Aldous","Briana","Casper","Delia","Emmett","Farah","Gideon","Hazel","Ivor","Junia","Kellan","Liora","Merritt","Nadia","Orson","Petra","Quincy","Rosalind","Silas","Tamsin","Ulric","Vera","Wendell","Xenia","Yusuf","Zelda","Ambrose","Beatrix","Corvin","Damaris"]
LAST = ["Blackwood","Calloway","Dunmore","Ellery","Fairbanks","Grimshaw","Halloway","Inkwell","Juniper","Kingsley","Lockhart","Marlowe","Nightingale","Osgood","Pemberton","Quill","Ravenshaw","Sterling","Thistledown","Underwood","Vanguard","Whitlock","Yardley","Zephyr","Ashford","Bramble","Copperfield","Drummond"]

PROJECT_IDEAS = {
"engineering": ["Design a footbridge for a park and present load calculations","Build a solar-powered water pump prototype","Prototype a low-cost prosthetic hand","Design a passive-cooling house for hot climates","Build a small wind-tunnel test rig","Create an earthquake-safe model tower","Design a rainwater harvesting system","Invent a better bicycle lock and stress-test it"],
"cs": ["Ship a full-stack web app with login and database","Write a compiler for a tiny language","Build a chat app with end-to-end encryption","Train an image classifier from scratch","Create a 2D game engine","Build a personal portfolio site with a blog engine","Contribute a real patch to an open-source project","Design a load-tested API service"],
"medicine": ["Run a community first-aid workshop","Build a nutrition plan for a local sports team","Create a public-health poster campaign","Shadow-chart a mock patient case file","Design a home-safety audit for seniors","Write an evidence review on a wellness claim","Build a mental-health resource guide for teens","Map local clinic access for your neighborhood"],
"law": ["Draft a complete small-business contract set","Hold a mock trial with classmates","Write a plain-language tenant-rights guide","Brief five landmark cases in your field","Draft a will and estate checklist","Build a startup legal-readiness kit","Argue both sides of a current legal debate","Create a know-your-rights pamphlet"],
"business": ["Write a full business plan and pitch it","Launch a micro-business with $100","Build a marketing campaign for a local shop","Create financial statements for a mock company","Design a brand identity package","Run a pricing experiment and report results","Write a market-research report on a trend","Draft an employee handbook"],
"science": ["Run a semester-long ecology field study","Build a weather station and publish data","Grow crystals and document the process","Test local water quality and report","Build a model rocket with telemetry","Catalog biodiversity in a city block","Replicate a classic experiment","Write a citizen-science project proposal"],
"math": ["Prove a theorem and present the proof","Build a statistical model of a sport","Create a math puzzle book for kids","Model loan payoff strategies in a spreadsheet","Write an explainer on a famous unsolved problem","Design a board game driven by probability","Analyze a dataset and publish findings","Build geometric art with code"],
"arts": ["Produce a short film","Mount a gallery show of your work","Publish a chapbook of poems","Compose and record an original song","Write and stage a one-act play","Create a photo essay on your town","Design a poster series for a cause","Keep a year-long sketchbook"],
"education": ["Design a full 6-week unit plan","Tutor a struggling student for a month","Build a classroom library on a budget","Create an assessment portfolio","Film yourself teaching and reflect","Design an inclusive lesson for all learners","Write a parent-communication handbook","Run a study-skills workshop"],
"trade": ["Wire a practice wall to code","Sweat-solder a copper manifold","Build a staircase to spec","Weld a certified test coupon","Service a full HVAC tune-up","Rebuild a small engine","Tile a bathroom floor mockup","Price a real job bid start to finish"],
"phd": ["Publish a literature review","Present at a (virtual) conference","Write a grant proposal draft","Complete a pilot study","Build an open dataset","Write a methods preprint","Defend a dissertation chapter","Launch a research collaboration"],
}

NOTES = {
 "medicine": " I am not a licensed medical professional — for health decisions, always consult a qualified clinician.",
 "law": " I am not a lawyer and this is not legal advice — consult a licensed attorney for legal matters.",
 "business": " I am not a licensed financial advisor — consult a qualified professional for financial decisions.",
}

def patent_pool():
    """Real publication numbers from the live patent catalog."""
    nums = []
    try:
        with open(os.path.expanduser("~/workspace/cyber-patent-catalog/data/patents.jsonl")) as f:
            for i, line in enumerate(f):
                if i >= 4000: break
                try: nums.append(json.loads(line)["publication_number"])
                except Exception: pass
    except FileNotFoundError:
        pass
    return nums or ["US2024000001A1"]

def main():
    patents = patent_pool()
    courses, idx, labs, projects = [], [], [], []
    n = 0
    college_rows = []
    for ckey, cname, abbr, tagline in COLLEGES:
        topics = TOPICS[ckey]
        pats = {"trade": TRADE_PATTERNS, "phd": PHD_PATTERNS}.get(ckey, STD_PATTERNS)
        words = WORDS[ckey]
        start = n + 1
        for ti, topic in enumerate(topics):
            for pi, (pfmt, level) in enumerate(pats):
                n += 1
                cid = "JAH-COURSE-%06d" % n
                title = pfmt.format(topic)
                code = "%s %d" % (abbr, level)
                lname = LEVEL_NAMES[level]
                credits = {101:3,201:3,301:4,401:4,501:3,601:6}[level]
                desc = random.choice(DESC_T).format(title=title, lname=lname,
                    cname=cname.lower().replace("college of ","").replace("trade school","the trades").replace("phd research college","doctoral research"),
                    t=topic, out=random.choice(OUTCOMES), code=code)
                # syllabus: 6 modules x 4 lessons
                mods = []
                for mi in range(6):
                    mtitle = MODULES[(ti + pi + mi) % len(MODULES)] + ": " + topic
                    lessons = [LESSON_FRAMES[(ti + pi + mi + li) % len(LESSON_FRAMES)].format(topic)
                               for li in range(4)]
                    mods.append({"m": mtitle, "lessons": lessons})
                # readings
                readings = []
                for wi in range(3):
                    w = words[(ti + pi + wi) % len(words)]
                    readings.append({"t":"dict","label":"Dictionary: "+w,"url":URLS["dict"]+w})
                w = words[(ti + pi) % len(words)]
                readings.append({"t":"wiki","label":"JAH Wiki: "+w,"url":URLS["wiki"]+w})
                readings.append({"t":"wiki","label":"JAH Wiki: "+topic,"url":URLS["wiki"]+topic.replace(" ","+")})
                sid = "JAH-SPEC-%06d" % random.randint(1, 438346)
                readings.append({"t":"spec","label":"Signature spec "+sid,"url":URLS["spec"]+sid})
                pno = patents[(n * 7919) % len(patents)]
                readings.append({"t":"patent","label":"Patent record "+pno,"url":URLS["patent"]+pno})
                readings.append({"t":"book","label":"Signature Books shelf","url":URLS["books"]})
                # teacher
                tname = random.choice(FIRST) + " " + random.choice(LAST)
                ttitle = {"trade":"Master Craftsman","phd":"Dr.","medicine":"Dr.","law":"Professor"}.get(ckey,"Professor")
                note = NOTES.get(ckey, "")
                persona = PERSONA_T.format(name=tname, title=title, t=topic, note=note)
                # labs
                clabs = [{"t":"Lab %d: %s — %s" % (li+1, lf[0], topic),
                          "d": lf[1].format(t=topic)} for li, lf in enumerate(LAB_FRAMES)]
                # prereq: the 101/first-pattern course of same topic
                prereq = ("JAH-COURSE-%06d" % (start + ti*len(pats))) if pi > 0 else None
                course = {"id":cid,"code":code,"title":title,"college":cname,
                          "college_key":ckey,"level":level,"credits":credits,
                          "desc":desc,"modules":mods,"readings":readings,
                          "teacher":{"name":tname,"title":ttitle,"persona":persona},
                          "labs":clabs,"prereq":prereq}
                courses.append(course)
                idx.append({"i":cid,"c":code,"t":title,"k":ckey,"l":level})
                for lb in clabs:
                    labs.append({"course":cid,"ctitle":title,"college":cname,
                                 "ckey":ckey,"t":lb["t"],"d":lb["d"]})
        # projects for this college
        for pti, p in enumerate(PROJECT_IDEAS[ckey]):
            projects.append({"id":"JAH-PROJECT-%06d" % (len(projects)+1),
                             "college":cname,"ckey":ckey,"t":p,
                             "d":"Capstone project for %s students: plan it, build it, document it, and present it." % cname})
        college_rows.append({"key":ckey,"name":cname,"abbr":abbr,"tagline":tagline,
                             "courses":len(topics)*len(pats),
                             "first_id":"JAH-COURSE-%06d" % start,
                             "last_id":"JAH-COURSE-%06d" % n})
        print("college", ckey, "done:", len(topics)*len(pats))
    # write chunks of 100
    for ci in range(0, len(courses), 100):
        with open(os.path.join(CHUNKS, "c%04d.json" % (ci//100+1)), "w") as f:
            json.dump(courses[ci:ci+100], f, separators=(",",":"))
    # compact index (plain json; small enough)
    with open(os.path.join(DATA, "courses.idx.json"), "w") as f:
        json.dump(idx, f, separators=(",",":"))
    with open(os.path.join(DATA, "colleges.json"), "w") as f:
        json.dump({"total": n, "colleges": college_rows,
                   "updated": "2026-10-01",
                   "by": "Justin Addam Higgins"}, f, indent=1)
    with open(os.path.join(DATA, "labs.json"), "w") as f:
        json.dump(labs, f, separators=(",",":"))
    with open(os.path.join(DATA, "projects.json"), "w") as f:
        json.dump(projects, f, separators=(",",":"))
    # degrees per college
    degs = []
    for ckey, cname, abbr, tag in COLLEGES:
        if ckey == "trade":
            names = [("Apprentice Certificate",6,101),("Journeyman Diploma",14,201),
                     ("Master Craftsman Degree",24,301)]
        elif ckey == "phd":
            names = [("Graduate Certificate",6,501),("Master of Research",12,501),
                     ("Doctor of Philosophy (PhD)",18,601)]
        else:
            names = [("Certificate",6,101),("Associate Degree",14,201),
                     ("Bachelor's Degree",28,301),("Master's Degree",16,401)]
        for di,(dname,need,minlv) in enumerate(names):
            did = "JAH-DEGREE-%s-%d" % (abbr, di+1)
            degs.append({"id":did,"college":cname,"ckey":ckey,"name":dname,
                         "need":need,"min_level":minlv,
                         "d":"Complete %d %s courses (%s level %d or higher) to earn the %s." %
                           (need, cname, "at" if minlv>101 else "any", minlv, dname)})
    with open(os.path.join(DATA, "degrees.json"), "w") as f:
        json.dump(degs, f, indent=1)
    print("TOTAL courses:", n)

if __name__ == "__main__":
    main()
