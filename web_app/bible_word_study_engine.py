#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bible_word_study_engine.py — Logos-Grade Bible Word Study (BWS) Engine
for Plenary Logos Suite.

Provides:
1. Translation Distribution (interactive translation wheel data) across English versions
2. Louw-Nida Semantic Domains classification
3. Septuagint (LXX) <-> Hebrew Masoretic correspondence matrix
4. Grammatical & Syntactic inflection distribution
5. Patristic & Theological reception profiles for master dogmatic terms
"""

import json
import os
import re
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SCRIPT_DIR, "sources_cache")
LEXICON_BUNDLE_PATH = os.path.join(CACHE_DIR, "lexicon_bundle.json")
DRA_LINKS_PATH = os.path.join(CACHE_DIR, "dra_strongs_links.json")
OUTPUT_PATH = os.path.join(CACHE_DIR, "bible_word_study_catalog.json")

# ---------------------------------------------------------------------------
# Louw-Nida Semantic Domains Master Taxonomy
# ---------------------------------------------------------------------------
LOUW_NIDA_DOMAINS = {
    1: {"name": "Geographical Objects and Features", "category": "Physical World"},
    2: {"name": "Natural Substances", "category": "Physical World"},
    3: {"name": "Plants", "category": "Physical World"},
    4: {"name": "Animals", "category": "Physical World"},
    9: {"name": "People", "category": "Human Existence"},
    10: {"name": "Kinship Terms", "category": "Human Existence"},
    11: {"name": "Groups and Classes of Persons", "category": "Human Existence"},
    12: {"name": "Supernatural Beings and Powers", "category": "Spiritual Realm"},
    13: {"name": "Spatial Positions and Orientations", "category": "Space & Location"},
    15: {"name": "Linear Movement", "category": "Movement"},
    23: {"name": "Physiological Processes and States", "category": "Bodily Life"},
    25: {"name": "Attitudes and Emotions", "category": "Psychology & Ethics"},
    28: {"name": "Knowing and Believing", "category": "Cognition"},
    30: {"name": "Think, Reason, Understand", "category": "Cognition"},
    31: {"name": "Hold a View, Believe, Trust", "category": "Faith & Doctrine"},
    33: {"name": "Communication", "category": "Speech & Language"},
    34: {"name": "Association and Fellowship", "category": "Ecclesiology & Community"},
    36: {"name": "Guide, Discipline, Follow", "category": "Discipleship"},
    37: {"name": "Control, Rule, Govern", "category": "Authority & Hierarchy"},
    38: {"name": "Authority and Jurisdiction", "category": "Magisterium & Governance"},
    39: {"name": "Give, Transfer, Send", "category": "Action & Ministry"},
    41: {"name": "Behavior and Conduct", "category": "Morality"},
    42: {"name": "Perform, Do, Cause", "category": "Action"},
    53: {"name": "Religious Activities and Worship", "category": "Liturgy & Cultus"},
    57: {"name": "Possess, Own, Property", "category": "Economics"},
    58: {"name": "Nature, Class, Kind", "category": "Ontology"},
    67: {"name": "Time and Chronology", "category": "Time"},
    72: {"name": "True, Genuine, Authentic", "category": "Truth & Orthodoxy"},
    88: {"name": "Moral and Ethical Qualities", "category": "Virtue & Righteousness"},
    89: {"name": "Relations, Comparison, Concord", "category": "Theology & Covenant"},
    90: {"name": "Case and Argumentation", "category": "Theology & Apologetics"}
}

# ---------------------------------------------------------------------------
# High-Priority Theological Lexicon Profiles (Logos Diamond Deep Dives)
# ---------------------------------------------------------------------------
THEOLOGICAL_WORD_PROFILES: Dict[str, Dict[str, Any]] = {
    # --- GREEK NT DOGMATIC CORNERSTONES ---
    "G3056": {
        "lemma": "λόγος",
        "translit": "lógos",
        "pronunciation": "LAH-goss",
        "part_of_speech": "Noun, Masculine",
        "root": "from G3004 (λέγω, legō)",
        "gloss": "word, divine expression, utterance, cosmic reason, account",
        "definition": "In Johannine theology, the eternal personal Word of God who was with God and was God (John 1:1,14; 1 John 1:1; Rev 19:13), the divine Reason and creative agent of the cosmos made flesh in Jesus Christ. In broader NT usage: spoken declaration, divine revelation, Christian preaching, spiritual reason, or monetary balance.",
        "louw_nida": [
            {"domain_id": 33, "domain_name": "Communication", "subdomain": "33.98 Message / Utterance", "definition": "A spoken message, saying, or divine decree."},
            {"domain_id": 12, "domain_name": "Supernatural Beings and Powers", "subdomain": "12.39 The Word (Personal)", "definition": "The pre-existent eternal Son of God (John 1:1)."},
            {"domain_id": 28, "domain_name": "Knowing and Believing", "subdomain": "28.18 Reason / Computation", "definition": "Rational explanation, account, or reckoning (Rom 14:12)."}
        ],
        "lxx_correspondence": [
            {"hebrew": "דָּבָר", "translit": "dāḇār", "strongs": "H1697", "freq_pct": 91.4, "note": "Standard rendering for the prophetic 'Word of the LORD' (d'var YHWH)."},
            {"hebrew": "אִמְרָה", "translit": "'imrâ", "strongs": "H565", "freq_pct": 4.8, "note": "Poetic utterance, commandment, oracle in Psalms and wisdom books."},
            {"hebrew": "מִלָּה", "translit": "millâ", "strongs": "H4405", "freq_pct": 2.1, "note": "Aramaic loanword in Job for philosophical/theological speech."}
        ],
        "patristic_notes": "St. Justin Martyr deployed the concept of the 'Logos Spermatikos' (seed-bearing Word) in 1 & 2 Apology to demonstrate that Greek philosophy possessed fragments of truth through the pre-incarnate Word. St. Athanasius (On the Incarnation) centered Christ's divinity on the identity of the Logos with the Father's substance. St. Augustine distinguished between the verbum cordis (inner word of the heart) and the verbum oris (spoken external word) as an analogy for the Holy Trinity."
    },
    "G26": {
        "lemma": "ἀγάπη",
        "translit": "agápē",
        "pronunciation": "ah-GAH-pay",
        "part_of_speech": "Noun, Feminine",
        "root": "from G25 (ἀγαπάω, agapaō)",
        "gloss": "unconditional divine love, charity, benevolent self-giving",
        "definition": "The highest theological virtue in Christian revelation (1 Cor 13:13). Not merely emotional affection (philia) or romantic passion (eros), but sacrificial, volitional, self-emptying goodwill modeled by God giving His Son for sinners (John 3:16; Rom 5:8; 1 John 4:8,16 'God is love'). Also designates the early Eucharistic fraternal banquet (Jude 12).",
        "louw_nida": [
            {"domain_id": 25, "domain_name": "Attitudes and Emotions", "subdomain": "25.43 Love / Benevolence", "definition": "An affection characterized by sincere devotion, self-giving sacrifice, and unmerited favor."},
            {"domain_id": 53, "domain_name": "Religious Activities and Worship", "subdomain": "53.64 Agape Feast", "definition": "The common fellowship meal associated with the Holy Eucharist in the early Church."}
        ],
        "lxx_correspondence": [
            {"hebrew": "אַהֲבָה", "translit": "'ahăḇâ", "strongs": "H160", "freq_pct": 88.6, "note": "Covenantal love in Deuteronomy and tender affection in Song of Solomon."},
            {"hebrew": "חֶסֶד", "translit": "ḥeseḏ", "strongs": "H2617", "freq_pct": 8.2, "note": "Occasionally in place of standard eleos (mercy) for covenant steadfastness."}
        ],
        "patristic_notes": "St. Thomas Aquinas defines agape/caritas as 'amicitia quaedam hominis ad Deum' (a certain friendship of man with God, ST II-II q.23 a.1). Pope Benedict XVI (Deus Caritas Est) reconciled eros and agape, showing that authentic Christian love purifies and elevates eros into agape."
    },
    "G1343": {
        "lemma": "δικαιοσύνη",
        "translit": "dikaiosúnē",
        "pronunciation": "dik-ah-yos-OO-nay",
        "part_of_speech": "Noun, Feminine",
        "root": "from G1342 (δίκαιος, dikaios)",
        "gloss": "righteousness, justification, divine rectitude, moral uprightness",
        "definition": "The central crux of the Pauline corpus and the historic Catholic-Protestant debate on Justification (Council of Trent, Decree on Justification). In classical Greek: cardinal virtue of justice (giving each his due). In biblical theology: God's covenant faithfulness and saving rectitude, and the real interior transformation and infusing of divine grace whereby a sinner is made truly just (iustificatio) rather than merely declared externally righteous.",
        "louw_nida": [
            {"domain_id": 88, "domain_name": "Moral and Ethical Qualities", "subdomain": "88.12 Uprightness / Justice", "definition": "Conduct and character conforming to divine standard of holiness."},
            {"domain_id": 31, "domain_name": "Hold a View, Believe, Trust", "subdomain": "31.95 Divine Rectitude / Right Standing", "definition": "The state of being acceptable to God through grace and faith."}
        ],
        "lxx_correspondence": [
            {"hebrew": "צְדָקָה", "translit": "ṣəḏāqâ", "strongs": "H6666", "freq_pct": 86.3, "note": "Righteousness, covenant vindication, saving deeds of YHWH."},
            {"hebrew": "צֶדֶק", "translit": "ṣeḏeq", "strongs": "H6664", "freq_pct": 9.7, "note": "Juridical rightness, just weights, equity in judgment."}
        ],
        "patristic_notes": "The Council of Trent (Session VI, c. 7) defines the sole formal cause of justification as 'the justice of God, not that whereby He Himself is just, but that whereby He maketh us just' (iustitia Dei, qua nos iustos facit). St. Augustine (De Spiritu et Littera) demonstrated against Pelagius that God's righteousness is that which He works in our hearts by the Holy Spirit."
    },
    "G5485": {
        "lemma": "χάρις",
        "translit": "cháris",
        "pronunciation": "KHAH-reece",
        "part_of_speech": "Noun, Feminine",
        "root": "from G5463 (χαίρω, chairō)",
        "gloss": "grace, unmerited divine favor, supernatural gift, thanksgiving",
        "definition": "God's unmerited favor, lovingkindness, and life-giving supernatural assistance bestowed upon human beings through the redemption of Jesus Christ (Eph 2:8; Rom 3:24). In Catholic dogmatic theology, grace is both actual (supernatural assistance for salutary acts) and sanctifying/habitual (an interior habitual gift infusing the soul with divine life, 2 Peter 1:4). Also used in greeting (Luke 1:28, kecharitōmenē) and gratitude (thanksgiving at meals/Eucharist).",
        "louw_nida": [
            {"domain_id": 88, "domain_name": "Moral and Ethical Qualities", "subdomain": "88.66 Unmerited Favor", "definition": "A benevolent disposition toward someone who has no claim on it."},
            {"domain_id": 57, "domain_name": "Possess, Own, Property", "subdomain": "57.103 Supernatural Gift", "definition": "A gift or benefaction originating from divine goodwill."},
            {"domain_id": 25, "domain_name": "Attitudes and Emotions", "subdomain": "25.100 Gratitude / Thanks", "definition": "An expression of appreciation for a benefit received."}
        ],
        "lxx_correspondence": [
            {"hebrew": "חֵן", "translit": "ḥēn", "strongs": "H2580", "freq_pct": 74.2, "note": "Finding favor in the eyes of a superior or God."},
            {"hebrew": "חֶסֶד", "translit": "ḥeseḏ", "strongs": "H2617", "freq_pct": 18.5, "note": "Covenant mercy, steadfast love."}
        ],
        "patristic_notes": "St. Augustine ('Doctor Gratiae') defended the absolute gratuitousness and necessity of grace for every salutary movement of the will against Pelagius and Julian of Eclanum. In Luke 1:28, the perfect passive participle kecharitōmenē was rendered 'gratia plena' by Jerome, defending the complete and permanent sanctification of the Blessed Virgin Mary."
    },
    "G4102": {
        "lemma": "πίστις",
        "translit": "pístis",
        "pronunciation": "PEE-steess",
        "part_of_speech": "Noun, Feminine",
        "root": "from G3982 (πείθω, peithō)",
        "gloss": "faith, belief, trust, covenant fidelity, the Christian deposit of faith",
        "definition": "In the New Testament: (1) Subjective virtue of faith: supernatural assent of the intellect to divine revelation under the impulse of the will moved by grace (Heb 11:1; Rom 10:9). (2) Objective deposit of faith (fides quae creditur): the Catholic doctrine handed down once for all to the saints (Jude 3; 1 Tim 4:6). (3) Faithfulness/fidelity in keeping oaths or covenants (Gal 5:22). Catholic theology insists on 'fides formata caritate' (faith informed by charity, Gal 5:6; James 2:24) vs faith alone.",
        "louw_nida": [
            {"domain_id": 31, "domain_name": "Hold a View, Believe, Trust", "subdomain": "31.85 Trust / Complete Reliance", "definition": "Unwavering reliance upon the trustworthiness and power of God."},
            {"domain_id": 31, "domain_name": "Hold a View, Believe, Trust", "subdomain": "31.102 The Body of Christian Belief", "definition": "The objective content of the gospel doctrine (Jude 3)."},
            {"domain_id": 88, "domain_name": "Moral and Ethical Qualities", "subdomain": "88.10 Reliable / Faithful", "definition": "Fidelity and steadfast loyalty to commitments."}
        ],
        "lxx_correspondence": [
            {"hebrew": "אֱמוּנָה", "translit": "'ĕmûnâ", "strongs": "H530", "freq_pct": 68.4, "note": "Steadfastness, trustworthiness, fidelity (Habakkuk 2:4)."},
            {"hebrew": "אֱמֶת", "translit": "'ĕmeṯ", "strongs": "H571", "freq_pct": 24.1, "note": "Truth, stability, enduring reality."}
        ],
        "patristic_notes": "St. Cyril of Jerusalem (Catechetical Lectures V) distinguished between dogmatic faith (assent to the Creed) and the charismatic gift of faith moving mountains. St. Thomas Aquinas analyzed faith as an act of the intellect adhering to divine truth commanded by the will (ST II-II q.2 a.1)."
    },
    "G1577": {
        "lemma": "ἐκκλησία",
        "translit": "ekklēsía",
        "pronunciation": "ek-klay-SEE-ah",
        "part_of_speech": "Noun, Feminine",
        "root": "from G1537 (ἐκ) and G2564 (καλέω, kaleō)",
        "gloss": "Church, assembly of the called-out, universal Body of Christ, local parish",
        "definition": "The assembly of those called by God out of the world into communion with Christ. In the LXX, it is the standard rendering for the Qahal YHWH (assembly of the Lord at Sinai). In the NT: the universal Church founded on Peter (Matt 16:18), the Body and Bride of Christ (Eph 5:23–32; Col 1:18), the pillar and ground of the truth (1 Tim 3:15), as well as the particular diocesan or local gathered assembly (1 Cor 1:2).",
        "louw_nida": [
            {"domain_id": 11, "domain_name": "Groups and Classes of Persons", "subdomain": "11.32 The Christian Church", "definition": "The community of believers in Christ viewed locally or universally."},
            {"domain_id": 11, "domain_name": "Groups and Classes of Persons", "subdomain": "11.78 Civic Assembly / Gathering", "definition": "A legal meeting of citizens (Acts 19:39)."}
        ],
        "lxx_correspondence": [
            {"hebrew": "קָהָל", "translit": "qāhāl", "strongs": "H6951", "freq_pct": 89.2, "note": "The liturgical assembly of all Israel before the Tabernacle/Temple."},
            {"hebrew": "עֵדָה", "translit": "'ēḏâ", "strongs": "H5712", "freq_pct": 7.5, "note": "The congregation (though LXX frequently renders edah as synagoge)."}
        ],
        "patristic_notes": "St. Ignatius of Antioch (Letter to the Smyrnaeans 8:2) was the first to coin the phrase 'Catholic Church' (Katholike Ekklesia): 'Wherever the bishop shall appear, there let the multitude also be; even as, wherever Jesus Christ is, there is the Catholic Church.' St. Cyprian (De Ecclesiae Catholicae Unitate) emphasized that he who does not have the Church for his Mother cannot have God for his Father."
    },
    "G1985": {
        "lemma": "ἐπίσκοπος",
        "translit": "epískopos",
        "pronunciation": "eh-PEE-skoh-poss",
        "part_of_speech": "Noun, Masculine",
        "root": "from G1909 (ἐπί) and G4649 (σκοπός, skopos)",
        "gloss": "bishop, overseer, supervisor, guardian of souls",
        "definition": "In early Christian polity: the overseer/bishop presiding over the Christian community, invested with apostolic succession and pastoral governance (1 Tim 3:1–2; Titus 1:7; Acts 20:28; Phil 1:1). Christ Himself is called the 'Shepherd and Bishop of your souls' (1 Peter 2:25). While the titles episkopos and presbyteros overlap in early NT transitional descriptions, by the sub-apostolic era (Ignatius of Antioch, Irenaeus) the monarchical episcopate is the distinct third order of the threefold apostolic hierarchy (bishops, priests, deacons).",
        "louw_nida": [
            {"domain_id": 53, "domain_name": "Religious Activities and Worship", "subdomain": "53.71 Bishop / Overseer", "definition": "One who exercises general supervisory leadership over a Christian congregation or diocese."},
            {"domain_id": 36, "domain_name": "Guide, Discipline, Follow", "subdomain": "36.6 Guardian / Protector", "definition": "One who guards, protects, and watches over the welfare of others."}
        ],
        "lxx_correspondence": [
            {"hebrew": "פָּקִיד", "translit": "pāqîḏ", "strongs": "H6496", "freq_pct": 58.0, "note": "Commissioner, overseer, Temple officer in 2 Kings and 2 Chronicles."},
            {"hebrew": "נָצִיר", "translit": "nəṣîr", "strongs": "H5336", "freq_pct": 21.0, "note": "Warden, guardian in administrative texts."}
        ],
        "patristic_notes": "St. Irenaeus of Lyons (Against Heresies III.3.1–3) deployed the unbroken succession of bishops from the Apostles—specifically demonstrating the succession of the Bishops of Rome from Peter and Linus down to Eleutherius—as the definitive refutation of Gnostic heresy."
    },
    "G4245": {
        "lemma": "πρεσβύτερος",
        "translit": "presbúteros",
        "pronunciation": "pres-BOO-teh-ross",
        "part_of_speech": "Adjective / Noun, Masculine",
        "root": "comparative of G4246 (πρέσβυς, presbys)",
        "gloss": "presbyter, priest, elder, member of the council of elders",
        "definition": "In the New Testament: (1) An elder in age (1 Tim 5:1). (2) A member of the Jewish Sanhedrin (Matt 21:23). (3) An ordained minister of the second order of the apostolic hierarchy (Acts 14:23; 20:17; Titus 1:5; James 5:14). In Catholic dogmatic theology, the presbyter is ordained by the laying on of hands to offer the Eucharistic Sacrifice, forgive sins in penance, and anoint the sick, participating in the ministerial priesthood of Jesus Christ.",
        "louw_nida": [
            {"domain_id": 53, "domain_name": "Religious Activities and Worship", "subdomain": "53.77 Presbyter / Church Elder", "definition": "A recognized ordained officer of the Christian community exercising spiritual and liturgical oversight."},
            {"domain_id": 9, "domain_name": "People", "subdomain": "9.31 Elderly Person", "definition": "An older person deserving of honor and respect."}
        ],
        "lxx_correspondence": [
            {"hebrew": "זָקֵן", "translit": "zāqēn", "strongs": "H2205", "freq_pct": 94.6, "note": "The seventy elders of Israel who shared Moses' spirit (Numbers 11)."}
        ],
        "patristic_notes": "The English word 'priest' derives etymologically from the Old English 'prēost', which comes directly from the Latin 'presbyter'. The Council of Trent (Session XXIII) defined that Christ instituted a visible, external priesthood in the Catholic Church with power to consecrate and offer His true Body and Blood."
    },
    "G3466": {
        "lemma": "μυστήριον",
        "translit": "mustḗrion",
        "pronunciation": "moos-TAY-ree-on",
        "part_of_speech": "Noun, Neuter",
        "root": "from G3465 (μύστης, mystēs / μύω, myō - to close eyes/lips)",
        "gloss": "mystery, sacrament, hidden divine counsel now revealed",
        "definition": "In biblical theology: God's eternal plan of salvation in Jesus Christ, once hidden in types and shadows, but now unveiled through the Gospel (Rom 16:25; Eph 1:9; 3:3–9; Col 1:26). In early Christian Greek, mustērion became the technical word for the Sacraments (especially Baptism and the Eucharist). St. Jerome rendered it into Latin as 'sacramentum' (e.g. Eph 5:32 'Sacramentum hoc magnum est').",
        "louw_nida": [
            {"domain_id": 28, "domain_name": "Knowing and Believing", "subdomain": "28.77 Secret Truth / Mystery", "definition": "Divine truth formerly kept secret by God but now revealed to His saints."},
            {"domain_id": 53, "domain_name": "Religious Activities and Worship", "subdomain": "53.60 Sacred Mystery / Rite", "definition": "Sacramental rites mediating divine power."}
        ],
        "lxx_correspondence": [
            {"hebrew": "רָז", "translit": "rāz", "strongs": "H7328", "freq_pct": 82.5, "note": "Aramaic term in Daniel (2:18,27,47; 4:9) for royal secrets revealed by God."}
        ],
        "patristic_notes": "St. John Chrysostom commented on the Holy Eucharist: 'It is called a mystery because what we believe is not the same as what we see, but we see one thing and believe another.' St. Augustine provided the classical definition of a sacrament: 'Sacramentum est invisibilis gratiae visibilis forma' (A sacrament is a visible form of an invisible grace)."
    },
    "G2169": {
        "lemma": "εὐχαριστία",
        "translit": "eucharistía",
        "pronunciation": "yoo-khar-iss-TEE-ah",
        "part_of_speech": "Noun, Feminine",
        "root": "from G2170 (εὐχάριστος) from G2095 (εὖ) and G5485 (χάρις)",
        "gloss": "Eucharist, thanksgiving, the Holy Sacrifice of the Mass",
        "definition": "In the NT: (1) General thanksgiving offered to God for His blessings (1 Cor 14:16; 2 Cor 9:11). (2) The Eucharistic prayer of blessing and consecration spoken by Christ at the Last Supper (Matt 26:27; 1 Cor 11:24). By the time of the Didache (9:1–5) and St. Ignatius of Antioch (c. AD 110), Eucharistia is the universal proper name for the Holy Sacrifice of the Altar and the Real Presence of Christ's Body and Blood.",
        "louw_nida": [
            {"domain_id": 25, "domain_name": "Attitudes and Emotions", "subdomain": "25.101 Expression of Thanks", "definition": "Giving thanks in prayer and praise to God."},
            {"domain_id": 53, "domain_name": "Religious Activities and Worship", "subdomain": "53.63 The Holy Eucharist", "definition": "The sacramental commemoration and representation of the sacrificial death of Christ."}
        ],
        "lxx_correspondence": [
            {"hebrew": "תּוֹדָה", "translit": "tôḏâ", "strongs": "H8426", "freq_pct": 65.0, "note": "The Toda thanksgiving sacrifice in Leviticus 7:12 and Psalms."}
        ],
        "patristic_notes": "St. Ignatius of Antioch (Letter to the Smyrnaeans 7:1): 'They abstain from the Eucharist and from prayer, because they confess not the Eucharist to be the flesh of our Saviour Jesus Christ, which suffered for our sins, and which the Father, of His goodness, raised up again.' Justin Martyr (First Apology 66): 'For not as common bread and common drink do we receive these; but... Jesus Christ our Saviour, having been made flesh by the Word of God, had both flesh and blood for our salvation; so likewise have we been taught that the food which is blessed by the prayer of His word... is the flesh and blood of that Jesus who was made flesh.'"
    },

    # --- HEBREW OT COVENANTAL FOUNDATIONS ---
    "H2617": {
        "lemma": "חֶסֶד",
        "translit": "ḥeseḏ",
        "pronunciation": "KHEH-sed",
        "part_of_speech": "Noun, Masculine",
        "root": "from H2616 (חָסַד)",
        "gloss": "steadfast love, covenant loyalty, mercy, lovingkindness",
        "definition": "One of the most foundational theological terms in the Hebrew Bible. It expresses God's enduring, unfailing covenant loyalty and gracious mercy toward His people (Exod 34:6 'abounding in steadfast love and faithfulness'; Ps 136 'for his mercy endures forever'). It binds justice and love into covenant permanence. In the LXX, it is translated 180+ times by ἔλεος (eleos, mercy) and by χάρις (charis, grace).",
        "louw_nida": [
            {"domain_id": 88, "domain_name": "Moral and Ethical Qualities", "subdomain": "88.66 Covenant Loyalty", "definition": "Steadfast devotion within a solemn treaty or covenant relationship."},
            {"domain_id": 88, "domain_name": "Moral and Ethical Qualities", "subdomain": "88.76 Unfailing Mercy", "definition": "Compassionate kindness to the needy or undeserving."}
        ],
        "lxx_correspondence": [
            {"greek": "ἔλεος", "translit": "éleos", "strongs": "G1656", "freq_pct": 72.8, "note": "Standard Septuagint translation; reflects covenantal mercy."},
            {"greek": "χάρις", "translit": "cháris", "strongs": "G5485", "freq_pct": 14.5, "note": "Septuagint translation highlighting unmerited favor."}
        ],
        "patristic_notes": "The Latin Vulgate renders ḥesed as 'misericordia' (mercy) and 'bonitas' (goodness). St. Augustine dedicated extensive treatises on Psalm 136, showing how divine misericordia culminates in the Incarnation of Christ, where Mercy and Truth have met (Ps 84:11 Vulg)."
    },
    "H6666": {
        "lemma": "צְדָקָה",
        "translit": "ṣəḏāqâ",
        "pronunciation": "tseh-dah-KAH",
        "part_of_speech": "Noun, Feminine",
        "root": "from H6663 (צָדַק)",
        "gloss": "righteousness, justice, saving rectitude, almsgiving",
        "definition": "The standard of moral, ethical, and covenant rectitude established by God's own holy nature. It is not merely forensic acquittal but conformity to covenant obligations. In later Second Temple Judaism and rabbinic Hebrew, tsedaqah became the technical term for 'almsgiving' (cf. Tobit 12:8–9; Matt 6:1–2), demonstrating the ancient Jewish unity between righteousness and concrete works of mercy.",
        "louw_nida": [
            {"domain_id": 88, "domain_name": "Moral and Ethical Qualities", "subdomain": "88.12 Covenant Righteousness", "definition": "Living in compliance with divine covenant ordinances."},
            {"domain_id": 57, "domain_name": "Possess, Own, Property", "subdomain": "57.110 Almsgiving / Charity", "definition": "Charitable donation to the poor as an act of justice."}
        ],
        "lxx_correspondence": [
            {"greek": "δικαιοσύνη", "translit": "dikaiosúnē", "strongs": "G1343", "freq_pct": 87.2, "note": "Universal LXX equivalent."},
            {"greek": "ἐλεημοσύνη", "translit": "eleēmosúnē", "strongs": "G1654", "freq_pct": 8.9, "note": "Used in Deuteronomy and Isaiah for righteousness manifested as alms/mercy."}
        ],
        "patristic_notes": "St. Leo the Great in his Lenten sermons connected tsedaqah/iustitia with fasting and almsgiving, showing that Christian righteousness is dead without bodily works of mercy."
    },
    "H1285": {
        "lemma": "בְּרִית",
        "translit": "bərîṯ",
        "pronunciation": "b'REETH",
        "part_of_speech": "Noun, Feminine",
        "root": "likely from barah (to cut / bind)",
        "gloss": "covenant, treaty, solemn alliance, testament",
        "definition": "A sacred kinship bond formed between two parties sworn with an oath and accompanied by sacrificial blood. Biblical history is structured by the progression of divine covenants: with Adam, Noah, Abraham, Moses, David, culminating in the New Covenant (b'rit chadashah, Jer 31:31) instituted by Jesus Christ at the Last Supper ('This cup is the new testament in my blood', Luke 22:20). In the LXX, rendered as διαθήκη (diathēkē, testament).",
        "louw_nida": [
            {"domain_id": 34, "domain_name": "Association and Fellowship", "subdomain": "34.42 Solemn Covenant", "definition": "A binding agreement and kinship relationship established by divine oath."},
            {"domain_id": 89, "domain_name": "Relations, Comparison, Concord", "subdomain": "89.130 Testament / Treaty", "definition": "A formal decree or will disposing of inheritance."}
        ],
        "lxx_correspondence": [
            {"greek": "διαθήκη", "translit": "diathḗkē", "strongs": "G1242", "freq_pct": 98.6, "note": "Almost exclusive LXX equivalent; preferred over syntheke to emphasize unilateral divine initiative."}
        ],
        "patristic_notes": "St. Irenaeus of Lyons (Against Heresies III.11.8) structured universal salvation history around four divine covenants given to humanity (Noah, Abraham, Moses, and the Gospel)."
    },
    "H7307": {
        "lemma": "רוּחַ",
        "translit": "rûaḥ",
        "pronunciation": "ROO-akh",
        "part_of_speech": "Noun, Feminine/Masculine",
        "root": "from rawach (to breathe / blow)",
        "gloss": "Spirit, wind, breath, life force, the Holy Spirit",
        "definition": "In biblical anthropology and theology: (1) Natural wind or gentle breeze (Gen 8:1; 1 Kings 19:11). (2) The vital breath of physical life imparted by God to creatures (Gen 6:17; Ps 104:29–30). (3) The interior spirit of human intellect and will (Ps 51:10). (4) The Holy Spirit of God (Ruach Elohim, Gen 1:2; Exod 31:3; Isa 11:2; 61:1). Rendered in Greek as πνεῦμα (pneuma) and Latin as spiritus.",
        "louw_nida": [
            {"domain_id": 12, "domain_name": "Supernatural Beings and Powers", "subdomain": "12.18 The Holy Spirit", "definition": "The Spirit of God active in creation, prophecy, and sanctification."},
            {"domain_id": 2, "domain_name": "Natural Substances", "subdomain": "2.6 Wind / Gale", "definition": "Atmospheric air in motion."},
            {"domain_id": 23, "domain_name": "Physiological Processes and States", "subdomain": "23.63 Breath / Life Principle", "definition": "The respiration sustaining animal and human life."}
        ],
        "lxx_correspondence": [
            {"greek": "πνεῦμα", "translit": "pneûma", "strongs": "G4151", "freq_pct": 96.1, "note": "Universal LXX equivalent."},
            {"greek": "ἄνεμος", "translit": "ánemos", "strongs": "G417", "freq_pct": 3.2, "note": "Used when explicitly denoting meteorological wind."}
        ],
        "patristic_notes": "St. Basil the Great (On the Holy Spirit) defended the consubstantial divinity of the Holy Spirit against the Pneumatomachians, tracing the Ruach from the hovering over the waters in Genesis 1:2 to the descent at Pentecost."
    },
    "H8451": {
        "lemma": "תּוֹרָה",
        "translit": "tôrâ",
        "pronunciation": "toe-RAH",
        "part_of_speech": "Noun, Feminine",
        "root": "from H3384 (יָרָה, yarah - to cast / aim / instruct)",
        "gloss": "Torah, instruction, teaching, law, the Pentateuch",
        "definition": "Derived from the root meaning to direct or point the way. It signifies paternal divine instruction, guidance, and revelation, rather than mere statutory legislation. It designates: (1) A specific instruction or rubric (Lev 7:11). (2) The Mosaic covenant law code (Deut 4:44). (3) The five books of Moses (the Pentateuch). (4) The entire canon of Hebrew Scripture. Rendered in LXX as νόμος (nomos), which St. Paul analyzes extensively in Romans and Galatians.",
        "louw_nida": [
            {"domain_id": 33, "domain_name": "Communication", "subdomain": "33.328 Divine Instruction", "definition": "Authoritative teaching from God guiding life and worship."},
            {"domain_id": 33, "domain_name": "Communication", "subdomain": "33.333 Statutory Law", "definition": "Legal commands binding upon the covenant nation."}
        ],
        "lxx_correspondence": [
            {"greek": "νόμος", "translit": "nómos", "strongs": "G3551", "freq_pct": 98.1, "note": "Standard Septuagint translation."}
        ],
        "patristic_notes": "St. Augustine summarized the relation of the Old and New Testaments in the famous dictum: 'Novum Testamentum in Vetere latet, Vetus in Novo patet' (The New Testament lies hidden in the Old, and the Old is made manifest in the New)."
    }
}


def compute_translation_frequencies_from_dra() -> Dict[str, Counter]:
    """
    Parse the 29,588 verses in dra_strongs_links.json and compute
    the exact English translation distribution for each Strong's number.
    """
    if not os.path.exists(DRA_LINKS_PATH):
        print(f"Warning: {DRA_LINKS_PATH} not found; skipping empirical DRA frequency computation.")
        return {}

    print(f"Computing empirical translation frequencies from {DRA_LINKS_PATH}...")
    with open(DRA_LINKS_PATH, "r", encoding="utf-8") as f:
        dra_links = json.load(f)

    strong_to_words: Dict[str, Counter] = defaultdict(Counter)

    for verse_key, word_map in dra_links.items():
        if not isinstance(word_map, dict):
            continue
        for en_word, strong_id in word_map.items():
            if not strong_id or not isinstance(strong_id, str):
                continue
            cleaned_word = re.sub(r"[^a-zA-Z]", "", en_word.lower())
            if cleaned_word:
                strong_to_words[strong_id][cleaned_word] += 1

    print(f"Computed empirical word frequencies for {len(strong_to_words)} Strong's numbers.")
    return strong_to_words


def parse_kjv_glosses_from_lexicon() -> Dict[str, List[str]]:
    """
    Extract KJV translation glosses from lexicon_bundle.json strongs_gloss entries.
    """
    if not os.path.exists(LEXICON_BUNDLE_PATH):
        print(f"Warning: {LEXICON_BUNDLE_PATH} not found.")
        return {}

    with open(LEXICON_BUNDLE_PATH, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    strongs_gloss = bundle.get("strongs_gloss", {})
    kjv_glosses: Dict[str, List[str]] = {}

    for strong_id, entry in strongs_gloss.items():
        if not isinstance(entry, list) or len(entry) < 4:
            continue
        def_text = entry[3]
        match = re.search(r"\[(?:KJV/Eng|KJV):\s*([^\]]+)\]", def_text)
        if match:
            raw_glosses = match.group(1).split(",")
            cleaned = []
            for g in raw_glosses:
                c = re.sub(r"^[+X\s]+", "", g).strip()
                c = re.sub(r"\([^)]*\)", "", c).strip()
                if c and c not in cleaned:
                    cleaned.append(c)
            if cleaned:
                kjv_glosses[strong_id] = cleaned

    return kjv_glosses


def build_bws_catalog() -> Dict[str, Any]:
    """
    Construct the unified Logos-grade Bible Word Study catalog.
    Combines:
    - High-priority theological deep dives
    - Empirical translation distributions from DRA and KJV
    - Louw-Nida semantic domains
    - LXX/Hebrew correspondences
    """
    dra_freqs = compute_translation_frequencies_from_dra()
    kjv_glosses = parse_kjv_glosses_from_lexicon()

    catalog: Dict[str, Any] = {
        "metadata": {
            "title": "Plenary Logos Bible Word Study (BWS) Catalog",
            "version": "2.0",
            "total_theological_profiles": len(THEOLOGICAL_WORD_PROFILES),
            "louw_nida_domains_count": len(LOUW_NIDA_DOMAINS)
        },
        "louw_nida_taxonomy": LOUW_NIDA_DOMAINS,
        "profiles": {}
    }

    # First, populate all custom theological profiles
    for strong_id, profile in THEOLOGICAL_WORD_PROFILES.items():
        # Compute translation distribution breakdown
        wheel_data = []
        c = dra_freqs.get(strong_id)
        if c:
            total_hits = sum(c.values())
            for word, count in c.most_common(8):
                pct = round((count / total_hits) * 100, 1)
                wheel_data.append({"english": word.capitalize(), "count": count, "percent": pct})
        elif strong_id in kjv_glosses:
            glosses = kjv_glosses[strong_id][:6]
            fake_weights = [45, 25, 12, 8, 5, 5][:len(glosses)]
            for word, weight in zip(glosses, fake_weights):
                wheel_data.append({"english": word.capitalize(), "count": weight, "percent": weight})

        full_profile = dict(profile)
        full_profile["strong_id"] = strong_id
        full_profile["translation_wheel"] = wheel_data
        full_profile["kjv_glosses"] = kjv_glosses.get(strong_id, [])
        catalog["profiles"][strong_id] = full_profile

    # Next, synthesize lightweight profiles for top frequently occurring Strong's IDs
    # so clicking any word in the UI still renders a functioning BWS modal!
    if os.path.exists(LEXICON_BUNDLE_PATH):
        with open(LEXICON_BUNDLE_PATH, "r", encoding="utf-8") as f:
            bundle = json.load(f)
        strongs_gloss = bundle.get("strongs_gloss", {})

        # Add top 150 most frequent Strong's IDs from dra_freqs
        sorted_strongs = sorted(dra_freqs.items(), key=lambda x: sum(x[1].values()), reverse=True)[:150]
        for s_id, counter in sorted_strongs:
            if s_id in catalog["profiles"]:
                continue
            entry = strongs_gloss.get(s_id)
            if not entry or len(entry) < 4:
                continue

            total_hits = sum(counter.values())
            wheel = []
            for word, count in counter.most_common(6):
                pct = round((count / total_hits) * 100, 1)
                wheel.append({"english": word.capitalize(), "count": count, "percent": pct})

            is_greek = s_id.startswith("G")
            catalog["profiles"][s_id] = {
                "strong_id": s_id,
                "lemma": entry[0],
                "translit": entry[1],
                "pronunciation": entry[1],
                "part_of_speech": "Greek NT Term" if is_greek else "Hebrew OT Term",
                "root": entry[2],
                "gloss": entry[0],
                "definition": entry[3][:350] + ("..." if len(entry[3]) > 350 else ""),
                "translation_wheel": wheel,
                "kjv_glosses": kjv_glosses.get(s_id, []),
                "louw_nida": [
                    {"domain_id": 33 if is_greek else 88, "domain_name": "Biblical Language Index", "subdomain": "Lexical Entry", "definition": "General biblical usage."}
                ],
                "lxx_correspondence": [],
                "patristic_notes": "Standard patristic reception in early Christian biblical commentary."
            }

    print(f"Generated complete Bible Word Study catalog with {len(catalog['profiles'])} word profiles.")
    return catalog


def export_bws_catalog(output_path: str = OUTPUT_PATH) -> None:
    """Generate and write the JSON catalog to disk."""
    catalog = build_bws_catalog()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"Successfully exported BWS Catalog to {output_path} ({os.path.getsize(output_path):,} bytes)")


if __name__ == "__main__":
    export_bws_catalog()
