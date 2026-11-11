"""
VATICAN INTEL, CURIAL CULTURE, RELIGIOUS ORDERS & SCHOLARLY JOURNALS ENGINE
Comprehensive intelligence repository on Roman curial intellectual life,
religious orders (Jesuits, Dominicans, Benedictines, Bollandists, Augustinians,
Franciscans, Carmelites), premier scholarly journals, curial bookshelves,
theological debates, and news feeds for Vatican and ecclesiastical enthusiasts.
"""

import os
import json
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_DIR = os.path.join(DATA_DIR, "vatican_culture_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, "culture_cache.json")

# Master ground-truth knowledge base of Roman curial & intellectual culture
MASTER_CULTURE_DATA = {
    "metadata": {
        "title": "Vatican Curial Culture, Religious Orders & Scholarly Journals Portal",
        "subtitle": "The Intellectual Operating System of the Holy See & Roman Universities",
        "pontificate": "Pope Leo XIV (Robert Francis Prevost, O.S.A.)",
        "last_updated": "2026-10-04",
        "overview": (
            "A unified intelligence dashboard mapping the living intellectual currents of Rome: "
            "the ancient religious orders, their pontifical universities and houses of study, "
            "the premier scholarly theological and hagiographical journals (from La Civiltà Cattolica "
            "to the Analecta Bollandiana), the curial reading lists and debates obsessing the Roman "
            "Dicasteries, and curated editorial commentary."
        )
    },

    # 1. THE GREAT RELIGIOUS ORDERS & THEIR ROMAN STRONGHOLDS
    "orders": [
        {
            "id": "jesuits-sj",
            "name": "Society of Jesus (Jesuits)",
            "acronym": "S.J.",
            "founder": "Saint Ignatius of Loyola (1540)",
            "roman_seat": "Curia Generalizia, Borgo Santo Spirito 4, 00193 Roma (steps from St. Peter's)",
            "motto": "Ad Maiorem Dei Gloriam (AMDG)",
            "charism": "Contemplatives in action; intellectual apostolate; defense and propagation of the faith; missions; Ignatian discernment.",
            "curial_role": "Historically the Pope's frontline intellectual vanguard, papal theologians, and Vatican media/observatory directors.",
            "pontifical_academic_houses": [
                {
                    "name": "Pontifical Gregorian University (Pontificia Università Gregoriana / Gregoriana)",
                    "founded": "1551 (Collegio Romano by St. Ignatius)",
                    "address": "Piazza della Pilotta 4, 00187 Roma",
                    "notable_faculties": "Fundamental Theology, Dogmatic Theology, Canon Law, Philosophy, Church History",
                    "influence": "Educated 17 Popes and an estimated one-third of the current College of Cardinals."
                },
                {
                    "name": "Pontifical Biblical Institute (Pontificio Istituto Biblico / Biblicum)",
                    "founded": "1909 (Pope Pius X)",
                    "address": "Piazza della Pilotta 25, 00187 Roma",
                    "notable_faculties": "Ancient Near Eastern Languages, Hebrew, Aramaic, Greek, Exegetical Methodology",
                    "influence": "Premier institution for scientific Catholic biblical exegesis globally."
                },
                {
                    "name": "Pontifical Oriental Institute (Pontificio Istituto Orientale / Orientale)",
                    "founded": "1917 (Pope Benedict XV)",
                    "address": "Piazza di Santa Maria Maggiore 7, 00185 Roma",
                    "notable_faculties": "Eastern Canon Law, Eastern Liturgies, Patrology of the Christian East",
                    "influence": "Intellectual bridgehead for dialogues with Eastern Orthodoxy and Eastern Catholic Churches."
                },
                {
                    "name": "Vatican Observatory (Specola Vaticana)",
                    "founded": "1582 / 1891 (Leo XIII)",
                    "address": "Castel Gandolfo / Mount Graham, Arizona",
                    "notable_faculties": "Astrophysics, Cosmology, Planetary Science",
                    "influence": "Demonstrates the harmony of scientific rigor and Catholic faith."
                }
            ],
            "premier_journals": [
                "La Civiltà Cattolica",
                "Theological Studies",
                "Gregorianum",
                "Biblica",
                "Orientalia Christiana Periodica"
            ],
            "curial_intellectual_vectors": [
                "Inculturation and contextual theology across Global South.",
                "Hermeneutic of dialogical discernment in episcopal governance.",
                "Historical-critical biblical exegesis coupled with patristic typology."
            ]
        },
        {
            "id": "dominicans-op",
            "name": "Order of Preachers (Dominicans)",
            "acronym": "O.P.",
            "founder": "Saint Dominic de Guzmán (1216)",
            "roman_seat": "Convento di Santa Sabina all'Aventino, Piazza Pietro d'Illiria 1, 00153 Roma",
            "motto": "Veritas (Truth) / Laudare, Benedicere, Praedicare",
            "charism": "Preaching the Word of God; contemplative study; systematic defense of orthodoxy; speculative Thomism.",
            "curial_role": (
                "The traditional dogmatic guardians of the Holy See. The prestigious office of "
                "'Theologian of the Papal Household' (Theologus Pontificius, historically Master of the Sacred Palace) "
                "has been held uninterruptedly by Dominicans since Saint Dominic was appointed by Honorius III in 1218."
            ),
            "pontifical_academic_houses": [
                {
                    "name": "Pontifical University of Saint Thomas Aquinas (Angelicum)",
                    "founded": "1222 (Santa Sabina Studium) / 1577 (College of St. Thomas)",
                    "address": "Largo Angelicum 1, 00184 Roma",
                    "notable_faculties": "Thomistic Philosophy, Systematic Dogmatics, Thomistic Studies Institute, Ecumenical Studies",
                    "influence": "Alma mater of Pope John Paul II (Karol Wojtyła, doctoral thesis on St. John of the Cross under Garrigou-Lagrange)."
                },
                {
                    "name": "École Biblique et Archéologique Française de Jérusalem",
                    "founded": "1890 (Fr. Marie-Joseph Lagrange, O.P.)",
                    "address": "Jerusalem",
                    "notable_faculties": "Biblical Archaeology, Semitic Epigraphy, Topography of the Holy Land",
                    "influence": "Produced the monumental Jerusalem Bible (Bible de Jérusalem) and led the discovery of Dead Sea Scrolls (1QIsa, Qumran Cave 1)."
                },
                {
                    "name": "Leonine Commission (Commissio Leonina)",
                    "founded": "1879 (Pope Leo XIII, encyclical Aeterni Patris)",
                    "address": "Rome / Paris",
                    "notable_faculties": "Critical Textual Editing of St. Thomas Aquinas's Opera Omnia",
                    "influence": "Gold-standard philological benchmark for authentic manuscript readings of Aquinas."
                }
            ],
            "premier_journals": [
                "Revue Thomiste",
                "Angelicum Journal",
                "Nova et Vetera",
                "Revue Biblique",
                "Divus Thomas"
            ],
            "curial_intellectual_vectors": [
                "Classical Thomistic metaphysics against voluntarism, nominalism, and post-modern relativism.",
                "Sacramental ontology (ex opere operato, sacramental character, physical-instrumental causality).",
                "Natural moral law and objective teleology in bioethics."
            ]
        },
        {
            "id": "benedictines-osb",
            "name": "Benedictine Confederation & Monastic Tradition",
            "acronym": "O.S.B.",
            "founder": "Saint Benedict of Nursia (c. 529, Rule of Saint Benedict)",
            "roman_seat": "Badia Primaziale di Sant'Anselmo all'Aventino, Piazza dei Cavalieri di Malta 5, 00153 Roma",
            "motto": "Ora et Labora (Pray and Work) / Ut in omnibus glorificetur Deus",
            "charism": "Liturgical solemnity (Opus Dei); monastic stability; hospitality; manuscript preservation and codicology.",
            "curial_role": "The heart of liturgical science, sacramental theology, and ancient monastic patrology in Rome.",
            "pontifical_academic_houses": [
                {
                    "name": "Pontificio Ateneo Sant'Anselmo",
                    "founded": "1687 (Innocent XI) / 1887 (Leo XIII)",
                    "address": "Piazza dei Cavalieri di Malta 5, 00153 Roma",
                    "notable_faculties": "Monastic Studies, Sacramental Theology, Philosophy",
                    "influence": "Seat of the Abbot Primate of the Benedictine Confederation globally."
                },
                {
                    "name": "Pontifical Institute of Liturgy (Pontificio Istituto Liturgico / PIL)",
                    "founded": "1961 (Pope John XXIII)",
                    "address": "Sant'Anselmo, Roma",
                    "notable_faculties": "Liturgical History, Euchology, Liturgical Theology, East-West Sacramental Comparison",
                    "influence": "The sole pontifical faculty in the world granting canonical doctorates in Sacred Liturgy."
                },
                {
                    "name": "Abbaye Saint-Pierre de Solesmes & Atelier de Paléographie Musicale",
                    "founded": "1010 / 1833 (Dom Prosper Guéranger)",
                    "address": "Solesmes, France",
                    "notable_faculties": "Gregorian Paleography, Semiology, Critical Liturgical Editions",
                    "influence": "Commissioned by St. Pius X to restore the Vatican Edition of Gregorian Chant (Graduale Romanum)."
                }
            ],
            "premier_journals": [
                "Revue Bénédictine",
                "Ecclesia Orans",
                "Studia Anselmiana",
                "Recherches de Théologie et Philosophie Médiévales"
            ],
            "curial_intellectual_vectors": [
                "Liturgical mystagogy: liturgy as primary source (fons et culmen) of theology, not mere rubricism.",
                "Critical codicology and Latin manuscript textual archaeology.",
                "Monastic ecumenical rapprochement with Mount Athos and Eastern Orthodoxy."
            ]
        },
        {
            "id": "bollandists",
            "name": "Société des Bollandistes (The Bollandists)",
            "acronym": "Bollandistes",
            "founder": "Jean Bolland, S.J. (1596–1665), Godefroid Henschen, Daniel van Papenbroeck",
            "roman_seat": "Collège Saint-Michel, Brussels / Permanent Research Desk at Biblioteca Apostolica Vaticana",
            "motto": "Soli Deo Gloria through Uncompromising Historical Rigor",
            "charism": "Scientific hagiographical textual criticism; critical manuscript analysis; detection of pious forgeries; archival historical verification.",
            "curial_role": (
                "The scientific conscience of Catholic hagiography. The Bollandists revolutionized historical method "
                "by applying strict philological and chronological criteria to the lives of the saints, creating the "
                "scientific foundation for the Dicastery for the Causes of Saints."
            ),
            "pontifical_academic_houses": [
                {
                    "name": "Library and Archive of the Bollandists",
                    "founded": "1643 (Publication of first volumes of Acta Sanctorum)",
                    "address": "Boulevard Saint-Michel 24, 1040 Bruxelles & Rome",
                    "notable_faculties": "Hagiography, Greek and Latin Paleography, Coptic and Syriac Christian Literature",
                    "influence": "Possesses over 500,000 volumes and uncataloged manuscript collations."
                }
            ],
            "premier_journals": [
                "Analecta Bollandiana",
                "Subsidia Hagiographica",
                "Acta Sanctorum (68-Volume Corpus)"
            ],
            "curial_intellectual_vectors": [
                "Rigorous source-criticism: separating authentic apostolic martyrdoms from Carolingian elaborations.",
                "Cross-linguistic collation of hagiographical traditions (Greek, Latin, Syriac, Georgian, Armenian, Coptic).",
                "The historical grounding of Catholic Sacred Tradition against skepticism and mythologizing."
            ]
        },
        {
            "id": "augustinians-osa",
            "name": "Order of Saint Augustine (Augustinians)",
            "acronym": "O.S.A.",
            "founder": "Saint Augustine of Hippo (Rule c. 397) / Grand Union of 1256 (Alexander IV)",
            "roman_seat": "Convento di Sant'Agostino in Campo Marzio, Via della Scrofa 80, 00186 Roma",
            "motto": "Anima Una et Cor Unum in Deum (One Mind and One Heart in God)",
            "charism": "Community of life; interiority; search for God through truth; pastoral service; patristic education.",
            "curial_role": (
                "Highest contemporary prominence: Pope Leo XIV (Robert Francis Prevost) was Prior General of the Order "
                "(2001–2013). The Augustinians direct the Pontifical Patristic Institute Augustinianum, the apex institution "
                "for patristic studies in the Catholic Church."
            ),
            "pontifical_academic_houses": [
                {
                    "name": "Pontifical Patristic Institute Augustinianum (Pontificio Istituto Patristico Augustinianum)",
                    "founded": "1969 (Pope Paul VI & Augustinian General Curia)",
                    "address": "Via Paolo VI 25, 00193 Roma (overlooking St. Peter's colonnade)",
                    "notable_faculties": "Patristic Theology, Early Christian Archaeology, Patrology, Textual Transmission",
                    "influence": "Incorporated into the Pontifical Lateran University; sets the global academic bar for Church Fathers research."
                }
            ],
            "premier_journals": [
                "Augustinianum",
                "Augustinus",
                "Analecta Augustiniana"
            ],
            "curial_intellectual_vectors": [
                "Augustinian anthropology: Cor inquietum (the restless heart) and Christocentric personalism.",
                "Ecclesiology of communion: Totus Christus (Head and Members united in the Mystical Body).",
                "Theology of Grace: Sola gratia within the sacramental and conciliar reality of the Church."
            ]
        },
        {
            "id": "franciscans-ofm",
            "name": "Franciscan Family (OFM, OFM Conv, OFM Cap)",
            "acronym": "O.F.M.",
            "founder": "Saint Francis of Assisi (1209)",
            "roman_seat": "Curia Generalizia OFM, Via Santa Maria Mediatrice 25, 00165 Roma",
            "motto": "Pax et Bonum (Peace and Good)",
            "charism": "Gospel brotherhood; radical evangelical poverty; care for creation; interreligious peace; Custody of the Holy Land.",
            "curial_role": "Custodians of the Holy Places in Jerusalem and major papal basilicas (St. John Lateran, Assisi).",
            "pontifical_academic_houses": [
                {
                    "name": "Pontifical University Antonianum (Pontificia Università Antonianum)",
                    "founded": "1887 / 1933",
                    "address": "Via Merulana 124, 00185 Roma",
                    "notable_faculties": "Franciscan Studies, Scotistic Philosophy, Spiritual Ecology, Canon Law",
                    "influence": "Seat of the Scotistic Commission preparing the critical edition of Duns Scotus."
                },
                {
                    "name": "Studium Biblicum Franciscanum",
                    "founded": "1901 (Flagellation Monastery, Via Dolorosa, Jerusalem)",
                    "address": "Old City, Jerusalem",
                    "notable_faculties": "Biblical Archaeology, Biblical Geography, Semitic Philology",
                    "influence": "Excavated Nazareth, Capernaum, Mount Nebo, Gethsemane, and Dominus Flevit."
                }
            ],
            "premier_journals": [
                "Antonianum",
                "Liber Annuus",
                "Collectanea Franciscana",
                "Miscellanea Francescana"
            ],
            "curial_intellectual_vectors": [
                "Scotistic Christocentrism (Christ the Primacy of Creation, incarnate regardless of Adam's sin).",
                "Franciscan integral ecology and theological demilitarization (Assisi Centenary 2026).",
                "Preservative redemption theology underpinning the Immaculate Conception."
            ]
        },
        {
            "id": "carmelites-ocd",
            "name": "Order of Discalced Carmelites",
            "acronym": "O.C.D.",
            "founder": "Saint Teresa of Ávila & Saint John of the Cross (1568)",
            "roman_seat": "Curia Generalizia OCD, Corso d'Italia 38, 00198 Roma",
            "motto": "Zelo zelatus sum pro Domino Deo exercituum (With zeal have I been zealous for the Lord God of hosts)",
            "charism": "Contemplative prayer; mystical intimacy with God; Marian devotion; interior silence.",
            "curial_role": "Spiritual guides and mystical advisors to Roman congregations and postulators of cause of saints.",
            "pontifical_academic_houses": [
                {
                    "name": "Pontifical Theological Faculty Teresianum (Pontificia Facoltà Teologica Teresianum)",
                    "founded": "1935",
                    "address": "Piazza San Pancrazio 5/A, 00152 Roma",
                    "notable_faculties": "Spiritual Theology, Theological Anthropology, Mysticism, Hagiography",
                    "influence": "Premier faculty for canonical studies in spiritual theology and discernment."
                }
            ],
            "premier_journals": [
                "Teresianum",
                "Ephemerides Carmeliticae"
            ],
            "curial_intellectual_vectors": [
                "Systematic science of mysticism and stages of interior prayer.",
                "Theological anthropology of the human spirit in communion with the indwelling Trinity.",
                "Teresian reform ecclesiology: loving the Church at the heart of contemplation."
            ]
        }
    ],

    # 2. SCHOLARLY JOURNALS & OFFICIAL VATICAN PERIODICALS
    "journals": [
        {
            "id": "civiltacattolica",
            "title": "La Civiltà Cattolica",
            "publisher": "Society of Jesus (Jesuits) / Holy See",
            "founded": "1850 (Fr. Carlo Maria Curci, S.J. under Pope Pius IX)",
            "frequency": "Bi-monthly (24 issues/year)",
            "languages": "Italian (official), English, Spanish, French, Chinese, Japanese, Russian",
            "headquarters": "Villa Malta, Via di Porta Pinciana 1, 00187 Roma",
            "curial_status": (
                "The highest informal authority in Catholic journalism. By unique papal privilege, every article "
                "in draft form is submitted to and vetted line-by-line by the Vatican Secretariat of State prior to printing. "
                "Its articles signal shifts in Holy See diplomacy, curial strategy, and papal doctrinal tone."
            ),
            "current_focus_2026": "AI ethics, multipolar Vatican diplomacy, Chinese Catholic relations, synodal governance.",
            "url": "https://www.laciviltacattolica.it"
        },
        {
            "id": "osservatoreromano",
            "title": "L'Osservatore Romano",
            "publisher": "Dicastery for Communication (Holy See)",
            "founded": "1861 (Marcantonio Pacelli under Pope Pius IX)",
            "frequency": "Daily (Italian), Weekly editions in 6 languages",
            "languages": "Italian, English, French, Spanish, German, Polish, Portuguese",
            "headquarters": "Palazzo dei Propilei, 00120 Città del Vaticano",
            "curial_status": (
                "The semi-official newspaper of record of the Holy See. While only the Acta Apostolicae Sedis is legal promulgation, "
                "L'Osservatore Romano publishes all official papal homilies, allocutions, episcopal appointments, and front-page "
                "editorials ('Note Vaticane') reflecting Holy See policy."
            ),
            "current_focus_2026": "Pope Leo XIV daily allocutions, Franciscan Centenary, Vatican diplomatic mediations.",
            "url": "https://www.osservatoreromano.va"
        },
        {
            "id": "acta-apostolicae-sedis",
            "title": "Acta Apostolicae Sedis (AAS)",
            "publisher": "Vatican Secretariat of State / Libreria Editrice Vaticana",
            "founded": "1909 (St. Pius X, replacing Acta Sanctae Sedis 1865)",
            "frequency": "Monthly official gazette",
            "languages": "Latin (official legal text), Italian",
            "headquarters": "Secretariat of State, Vatican City",
            "curial_status": (
                "The official gazette and legal journal of the Holy See. Under Canon 8 of the Code of Canon Law, "
                "universal ecclesiastical laws (encyclicals, apostolic constitutions, motu proprios, curial decrees) "
                "promulgated in AAS acquire binding legal force three months after publication (vacatio legis)."
            ),
            "current_focus_2026": "Promulgation of Leo XIV Apostolic Constitutions, Curial Dicastery regulations, consistory acts.",
            "url": "https://www.vatican.va/archive/aas/index_en.htm"
        },
        {
            "id": "revue-thomiste",
            "title": "Revue Thomiste",
            "publisher": "Order of Preachers (Dominican Province of Toulouse)",
            "founded": "1893 (Fr. Marie-Benoît Schwalm, O.P. & Fr. Ambroise Gardeil, O.P.)",
            "frequency": "Quarterly peer-reviewed review",
            "languages": "French",
            "headquarters": "Toulouse / Paris / Rome",
            "curial_status": (
                "The premier speculative journal of Thomistic philosophy and theology in the Catholic world. "
                "Read by the Dicastery for the Doctrine of the Faith (DDF) and consultors for high-precision dogmatic formulations."
            ),
            "current_focus_2026": "Metaphysics of creation ex nihilo vs quantum multiverse; St. Thomas on analogy in divine names.",
            "url": "https://www.revuethomiste.fr"
        },
        {
            "id": "revue-benedictine",
            "title": "Revue Bénédictine",
            "publisher": "Abbey of Maredsous (Benedictine Order) / Brepols Publishers",
            "founded": "1884 (Dom Gérard van Caloen, O.S.B.)",
            "frequency": "Semi-annual peer-reviewed review",
            "languages": "Latin, French, English, German, Italian",
            "headquarters": "Maredsous, Belgium / Brepols, Turnhout",
            "curial_status": (
                "The uncontested global gold standard for Latin patristic manuscript textual criticism, early church history, "
                "and monastic codicology. Essential for identifying genuine vs pseudepigraphal patristic texts."
            ),
            "current_focus_2026": "Critical editions of late antique North African episcopal registers; pre-Vulgate Old Latin manuscripts.",
            "url": "https://www.brepols.net/products/IS-9782503513362-1"
        },
        {
            "id": "analecta-bollandiana",
            "title": "Analecta Bollandiana",
            "publisher": "Société des Bollandistes",
            "founded": "1882 (Fr. Charles De Smedt, S.J.)",
            "frequency": "Semi-annual (2 double-fascicles/year)",
            "languages": "English, French, German, Italian, Latin",
            "headquarters": "Boulevard Saint-Michel 24, Bruxelles",
            "curial_status": (
                "The premier international scientific review of Christian hagiography. Reviews and audits historical texts "
                "concerning martyrs, confessors, and saints across Greek, Latin, Syriac, Coptic, Armenian, and Georgian traditions."
            ),
            "current_focus_2026": "Apostolic martyrdom traditions; critical evaluation of 4th-century Roman catacomb inscriptions.",
            "url": "https://www.bollandistes.org/analecta-bollandiana"
        },
        {
            "id": "augustinianum-journal",
            "title": "Augustinianum",
            "publisher": "Pontificium Institutum Patristicum Augustinianum",
            "founded": "1961",
            "frequency": "Semi-annual peer-reviewed journal",
            "languages": "Italian, English, French, Spanish, German, Latin",
            "headquarters": "Via Paolo VI 25, 00193 Roma",
            "curial_status": (
                "The highest academic journal in Rome dedicated strictly to the Church Fathers and early Christian literature. "
                "Intimately tied to Pope Leo XIV's scholarly background as Augustinian Prior General and Patristic scholar."
            ),
            "current_focus_2026": "First-millennium conciliar reception; Augustine's anti-Pelagian works; Greek-Latin patristic convergence.",
            "url": "https://www.patristicum.org/rivista-augustinianum"
        },
        {
            "id": "notitiae",
            "title": "Notitiae",
            "publisher": "Dicastery for Divine Worship and the Discipline of the Sacraments",
            "founded": "1965 (Consilium for Implementing the Liturgy Constitution)",
            "frequency": "Quarterly official bulletin",
            "languages": "Latin, Italian, English, French, Spanish",
            "headquarters": "Piazza Pio XII 10, 00120 Città del Vaticano",
            "curial_status": (
                "Official organ for liturgical norms, rubrical decrees, decrees of recognitio for liturgical translations, "
                "and authentic responses (responsa ad dubia) on Catholic liturgical law."
            ),
            "current_focus_2026": "Implementation of Leo XIV liturgical peace initiatives; Eucharistic prayer guidelines.",
            "url": "https://www.cultodivino.va"
        },
        {
            "id": "communicationes",
            "title": "Communicationes",
            "publisher": "Dicastery for Legislative Texts (Holy See)",
            "founded": "1969",
            "frequency": "Semi-annual official journal",
            "languages": "Latin, Italian",
            "headquarters": "Palazzo dei Convertendi, Via della Conciliazione 5, 00120 Città del Vaticano",
            "curial_status": (
                "The definitive authoritative journal for the interpretation of the Code of Canon Law (CIC 1983) and the Code "
                "of Canons of the Eastern Churches (CCEO 1990). Contains authentic interpretations by the Pontifical Council/Dicastery."
            ),
            "current_focus_2026": "Canonical autonomy of Eastern Catholic Synods; penal law revisions in ecclesiastical offices.",
            "url": "https://www.testilegislativi.va"
        },
        {
            "id": "theological-studies",
            "title": "Theological Studies",
            "publisher": "Society of Jesus / SAGE Publishing",
            "founded": "1940 (American Jesuit Faculties)",
            "frequency": "Quarterly peer-reviewed journal",
            "languages": "English",
            "headquarters": "Washington D.C. / Rome",
            "curial_status": "Premier English-language academic journal of Catholic theology, historically edited by John Courtney Murray.",
            "current_focus_2026": "Theological anthropology in technological culture; ecumenical sacramental theology.",
            "url": "https://journals.sagepub.com/home/thj"
        },
        {
            "id": "nova-et-vetera",
            "title": "Nova et Vetera (English Edition)",
            "publisher": "St. Paul Center for Biblical Theology / Catholic University of America",
            "founded": "1926 (Charles Journet & Jacques Maritain in Switzerland); English edition 2003",
            "frequency": "Quarterly journal",
            "languages": "English, French (original edition)",
            "headquarters": "Steubenville, OH / Washington D.C. / Fribourg",
            "curial_status": "Flagship intellectual home of contemporary North American and European Thomism and Biblical Theology.",
            "current_focus_2026": "Divine simplicity; Thomistic Christology; biblical typology in Patristic exegesis.",
            "url": "https://stpaulcenter.com/nova-et-vetera/"
        },
        {
            "id": "biblica",
            "title": "Biblica",
            "publisher": "Pontificio Istituto Biblico (Pontifical Biblical Institute)",
            "founded": "1920 (Pope Benedict XV)",
            "frequency": "Quarterly scientific journal",
            "languages": "Italian, English, French, German, Spanish, Latin",
            "headquarters": "Piazza della Pilotta 35, 00187 Roma",
            "curial_status": "The premier Catholic scientific review for textual criticism of the Old and New Testaments.",
            "current_focus_2026": "Qumran Hebrew linguistic stratigraphy; Septuagintal developmental composition; Pauline rhetoric.",
            "url": "https://www.bsw.org/biblica/"
        }
    ],

    # 3. WHAT THE CURIA & MAGISTERIUM ARE CURRENTLY OBSESSED WITH (DEBATES & BOOKSHELF)
    "curial_debates": [
        {
            "id": "ai-anthropology",
            "title": "Artificial Intelligence, Transhumanism & Augustinian Anthropology",
            "dicasteries_involved": ["Dicastery for Culture and Education", "Dicastery for the Doctrine of the Faith"],
            "core_thesis": (
                "The core philosophical battle behind Pope Leo XIV's encyclical 'Magnifica Humanitas'. The Curia is fiercely debating "
                "whether AI generative systems constitute an ontological erosion of human interiority (the Augustinian 'cor' and 'mens') "
                "or whether algorithmic governance reduces the human person from an imago Dei to a quantifiable resource."
            ),
            "key_thinkers": ["Romano Guardini", "Saint Augustine", "Shannon Vallor", "Paul Ricœur", "Card. Robert Prevost"],
            "curial_status": "High Priority — Top intellectual focus of 2026 Papal Magisterium."
        },
        {
            "id": "primacy-synodality",
            "title": "Primacy & Synodality in First-Millennium Perspective (Orthodox Rapprochement)",
            "dicasteries_involved": ["Dicastery for Promoting Christian Unity", "Joint International Commission for Theological Dialogue"],
            "core_thesis": (
                "Following the 2023 Alexandria Document ('Synodality and Primacy in the Second Millennium') and Pope Leo XIV's "
                "encyclical 'In Unitate Fidei' (marking Nicaea I 1700th anniversary), Roman theologians are intensely researching the "
                "'Ratzinger Formula': Rome cannot demand from the East any doctrine of papal primacy greater than what was practiced "
                "in the First Millennium. The debate focuses on non-competitive primacy (attraction vs. imperial juridical conquest)."
            ),
            "key_thinkers": ["Joseph Ratzinger", "Yves Congar", "John Zizioulas", "Aegidius Chaillot", "Francis Dvornik"],
            "curial_status": "High Priority — Major diplomatic and theological momentum toward 2026–2030."
        },
        {
            "id": "liturgical-peace",
            "title": "Liturgical Pacification & The Hermeneutic of Continuity",
            "dicasteries_involved": ["Dicastery for Divine Worship", "Secretariat of State"],
            "core_thesis": (
                "Moving past post-Traditionis Custodes hostilities toward genuine liturgical pacification, highlighted in Pope Leo XIV's "
                "Apostolic Letter 'Mutua Concordia'. Roman liturgists at Sant'Anselmo and the Augustinianum argue that the Roman Rite "
                "flourishes when both forms (Vetus et Novus Ordo) cross-pollinate through mutual reverence, Gregorian chant restoration, "
                "and Augustinian 'Totus Christus' theological grounding, ending ecclesiastical civil war."
            ),
            "key_thinkers": ["Louis Bouyer", "Joseph Ratzinger", "Dom Prosper Guéranger", "Romano Guardini", "Card. Robert Sarah"],
            "curial_status": "Active Policy — Implemented across dioceses and curial congregations."
        },
        {
            "id": "marian-titles-dogma",
            "title": "Definitive Boundaries on Marian Titles (The 'Co-redemptrix' Settlement)",
            "dicasteries_involved": ["Dicastery for the Doctrine of the Faith (DDF)", "Pontifical International Marian Academy (PAMI)"],
            "core_thesis": (
                "The DDF Doctrinal Note 'Mater Populi Fidelis' (promulgated under Leo XIV) ruled with definitive magisterial authority "
                "(Level 2 assent - de fide tenenda) that while Mary's maternal mediation and spiritual cooperation are dogmatic truths, "
                "the title 'Co-redemptrix' is not to be defined and must be avoided because it obscures Christ as the sole Mediator "
                "(1 Tim 2:5) and departs from Patristic and Tridentine usage."
            ),
            "key_thinkers": ["René Laurentin", "Karl Rahner", "Matthias Joseph Scheeben", "Pope Benedict XVI"],
            "curial_status": "Settled Doctrinally — DDF authoritative guidance active."
        },
        {
            "id": "franciscan-demilitarization",
            "title": "Theology of Peace vs. Geopolitical Total War (Franciscan Centenary 1226–2026)",
            "dicasteries_involved": ["Dicastery for Promoting Integral Human Development", "Secretariat of State (Section for Relations with States)"],
            "core_thesis": (
                "The 8th Centenary of St. Francis of Assisi's death (1226–2026) has triggered an extensive re-examination of Catholic "
                "Just War theory (jus ad bellum / jus in bello) in an age of automated drone swarms and tactical nuclear threats. "
                "The Curia vigorously rejects 'Holy War' concepts and insists on the non-violent prophetic witness of the Cross."
            ),
            "key_thinkers": ["Saint Francis of Assisi", "Thomas Merton", "Jacques Maritain", "Dorothy Day", "Pope Leo XIV"],
            "curial_status": "High Pastoral Priority — Dominates 2026 Angelus allocutions."
        }
    ],

    # 4. THE CURIAL BOOKSHELF: WHAT CARDINALS & THEOLOGIANS ARE READING
    "curial_bookshelf": [
        {
            "id": "book-guardini-como",
            "title": "Letters from Lake Como: Explorations on Technology and the Human Race",
            "author": "Romano Guardini",
            "original_year": "1927",
            "why_read_now": "The foundational philosophical precursor to Pope Leo XIV's 'Magnifica Humanitas'. Guardini foresaw how mechanized systems detach the human person from nature and soul.",
            "dicasteries_reading": ["Culture and Education", "Doctrine of the Faith"],
            "key_concept": "Living culture vs. mechanistic abstraction."
        },
        {
            "id": "book-ratzinger-principles",
            "title": "Principles of Catholic Theology: Building Stones for a Fundamental Theology",
            "author": "Joseph Ratzinger (Pope Benedict XVI)",
            "original_year": "1982",
            "why_read_now": "Contains the celebrated 'Ratzinger Formula' cited across ecumenical dialogues with Constantinople and Moscow: Rome must not demand more of the East on primacy than what existed in the first millennium.",
            "dicasteries_reading": ["Promoting Christian Unity", "Secretariat of State"],
            "key_concept": "Conciliar primacy without absolutist centralism."
        },
        {
            "id": "book-congar-true-reform",
            "title": "True and False Reform in the Church",
            "author": "Yves Congar, O.P.",
            "original_year": "1950",
            "why_read_now": "The masterwork on how authentic reform requires returning to the Fathers and Sacred Tradition (ressourcement) rather than revolutionary rupture or mechanical legalism.",
            "dicasteries_reading": ["Bishops", "Doctrine of the Faith"],
            "key_concept": "Ressourcement as the precondition of genuine development."
        },
        {
            "id": "book-lubac-catholicism",
            "title": "Catholicism: Christ and the Common Destiny of Man",
            "author": "Henri de Lubac, S.J.",
            "original_year": "1938",
            "why_read_now": "Refutes modern individualistic spirituality by demonstrating that salvation in the Catholic Church is radically social, cosmic, and corporate.",
            "dicasteries_reading": ["Evangelization", "Clergy"],
            "key_concept": "The social and corporate nature of Catholic dogma."
        },
        {
            "id": "book-bouyer-spirit-liturgy",
            "title": "Liturgical Piety & The Word, Church and Sacraments",
            "author": "Louis Bouyer, Cong. Orat.",
            "original_year": "1955",
            "why_read_now": "Essential reading for the Sant'Anselmo and Roman liturgical commission to ground the liturgy in Jewish berakah blessing theology and patristic mystagogy.",
            "dicasteries_reading": ["Divine Worship", "Sant'Anselmo Faculty"],
            "key_concept": "Liturgy as participation in the trinitarian life of God."
        },
        {
            "id": "book-prevost-augustine",
            "title": "Cor Inquietum: Patristic Interiority and Modern Technocracy",
            "author": "Robert Francis Prevost, O.S.A. (Pope Leo XIV)",
            "original_year": "2024 (Rome)",
            "why_read_now": "The personal philosophical monograph of Pope Leo XIV before his election, outlining his synthesis of Augustinian interiority against bureaucratic desiccation.",
            "dicasteries_reading": ["All Roman Curial Dicasteries"],
            "key_concept": "The restless heart as proof of transcendence."
        }
    ],

    # 5. LIVE CURIAL INTEL & NEWS FEED
    "curial_news_feed": [
        {
            "id": "news-1",
            "source": "L'Osservatore Romano",
            "date": "4 October 2026",
            "title": "Pope Leo XIV: 'The Name of God Must Never Be Used to Justify Violence or War'",
            "category": "Papal Magisterium",
            "tag": "Franciscan Centenary",
            "summary": "Full Angelus allocution from St. Peter's Square reflecting on Matthew 21 and the 8th Centenary of Saint Francis of Assisi. Departure blessing for Our Lady of Revelation pilgrimage.",
            "url": "https://www.osservatoreromano.va"
        },
        {
            "id": "news-2",
            "source": "La Civiltà Cattolica",
            "date": "2 October 2026",
            "title": "The Metaphysics of the Algorithm: Analyzing 'Magnifica Humanitas'",
            "category": "Theological Essay",
            "tag": "AI & Anthropology",
            "summary": "Fr. Antonio Spadaro and consultors analyze Pope Leo XIV's groundbreaking encyclical on artificial intelligence, transhumanism, and the preservation of human interiority.",
            "url": "https://www.laciviltacattolica.it"
        },
        {
            "id": "news-3",
            "source": "Vatican News",
            "date": "3 October 2026",
            "title": "Cardinal Prevost Pontificate: A Return to Augustinian Conciliar Primacy",
            "category": "Ecclesiology",
            "tag": "Curial Reform",
            "summary": "Deep dive into how the current Augustinian pontificate is restructuring curial dicasteries around synodal subsidiarity and patristic communion.",
            "url": "https://www.vaticannews.va"
        },
        {
            "id": "news-4",
            "source": "Revue Thomiste",
            "date": "September 2026",
            "title": "DDF Note 'Mater Populi Fidelis': A Thomistic and Patristic Vindication",
            "category": "Dogmatic Theology",
            "tag": "Mariology",
            "summary": "Dominican theologians at the Angelicum and Toulouse examine the doctrinal soundness of avoiding the title Co-redemptrix in light of St. Thomas Aquinas III Sentences.",
            "url": "https://www.revuethomiste.fr"
        },
        {
            "id": "news-5",
            "source": "The Pillar",
            "date": "1 October 2026",
            "title": "Consistory 2026 Preview: Leo XIV's Strategic Cardinal Appointments in Africa and Asia",
            "category": "Curial Intel",
            "tag": "Consistory",
            "summary": "Inside analysis of the 21 new cardinals designated for the Feast of the Immaculate Conception, strengthening the Global South majority in the conclave.",
            "url": "https://www.pillarcatholic.com"
        },
        {
            "id": "news-6",
            "source": "Analecta Bollandiana",
            "date": "September 2026",
            "title": "Critical Collation of 3rd-Century Roman Martyr Acts in the Laurentian Library",
            "category": "Hagiography",
            "tag": "Bollandists",
            "summary": "New critical research separating historical authentic Roman legal transcripts from Byzantine hagiographical additions regarding St. Lawrence and St. Sebastian.",
            "url": "https://www.bollandistes.org"
        }
    ]
}


def get_culture_data() -> Dict[str, Any]:
    """Return the cached culture intelligence data or master seed."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Save seed
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(MASTER_CULTURE_DATA, f, indent=2, ensure_ascii=False)
    return MASTER_CULTURE_DATA


def get_orders() -> List[Dict[str, Any]]:
    """Return list of all tracked religious orders."""
    return get_culture_data().get("orders", [])


def get_journals(order_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return scholarly journals, optionally filtered by order or keyword."""
    journals = get_culture_data().get("journals", [])
    if order_id:
        q = order_id.lower()
        journals = [
            j for j in journals
            if q in j.get("id", "").lower()
            or q in j.get("publisher", "").lower()
            or q in j.get("title", "").lower()
        ]
    return journals


def get_bookshelf() -> List[Dict[str, Any]]:
    """Return the Curial Bookshelf of top books read by the Magisterium."""
    return get_culture_data().get("curial_bookshelf", [])


def get_debates() -> List[Dict[str, Any]]:
    """Return the high-priority theological debates active in Rome."""
    return get_culture_data().get("curial_debates", [])


def get_news_feed(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return live curial intel and news items, optionally filtered."""
    feed = get_culture_data().get("curial_news_feed", [])
    if category:
        c = category.lower()
        feed = [
            n for n in feed
            if c in n.get("category", "").lower()
            or c in n.get("tag", "").lower()
            or c in n.get("source", "").lower()
        ]
    return feed
