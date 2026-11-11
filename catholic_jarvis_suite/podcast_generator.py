"""
NotebookLM-Style Deep Dive Podcast Generator
Converts 'THE_CATHOLIC_CASE_Readers_Edition.md' into a multi-host conversational audio podcast.
Features:
  - Two AI Hosts: Rachel (en-US-AvaNeural) and Leo (en-US-ChristopherNeural)
  - Natural conversational banter, intellectual depth, concessions, and primary source revelations
  - Full audio synthesis via Edge TTS
  - Timestamped interactive transcript for live frontend playback
"""

import os
import io
import json
import time
import asyncio
import edge_tts
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PODCAST_DIR = os.path.join(DATA_DIR, "podcast_episodes")
os.makedirs(PODCAST_DIR, exist_ok=True)

AUDIO_OUTPUT = os.path.join(PODCAST_DIR, "catholic_case_deep_dive.mp3")
MANIFEST_OUTPUT = os.path.join(PODCAST_DIR, "catholic_case_deep_dive.json")

# Master Dialogue Script for The Catholic Case Deep Dive
# Replicating the authentic Google NotebookLM Deep Dive cadence and intellectual texture
PODCAST_SCRIPT = [
    # ACT I: THE OPENING HOOK & THE SPANISH BIBLE PARADOX
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+2%",
        "text": "Welcome back to the Deep Dive! Today, we are opening up an absolute powerhouse of a document. It's titled, The Faith That Was Already There: The Catholic Case Against the Myths and Theology of Mexican Pentecostalism."
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "And when you first see a title like that, you might expect standard, defensive apologetics. But this manuscript? It completely flips the script. It is thirty-three chapters of raw archival history, biblical philology, and street-level debate notes."
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+2%",
        "text": "Right! And the author's target isn't just generic Protestantism. It's the specific movements sweeping through Mexico, Southern California, and Mexican-American families from Jalisco to Sinaloa. We're talking about the Oneness Apostólicos, La Luz del Mundo, Armando Alducin, and the massive Assemblies of God networks."
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "Exactly. And the core argument that every single one of those preachers relies on is what you could call the 'Great Apostasy' story: the idea that the true Christian faith died out, Rome buried the Bible in darkness, and then God magically dug it back up at Azusa Street in 1906, or, as one founding story reportedly has it, at Villa Aldama in 1914."
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+3%",
        "text": "And the Catholic answer in this text is just brilliant. It says: 'Nothing needed digging up. The faith those preachers claim to have recovered was already there—publicly, visibly, and continuously.'"
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "And Rachel, let's start with the single biggest bombshell in the historical section. Because every Mexican evangelical pastor carries one specific Bible into the pulpit: the Reina-Valera."
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+2%",
        "text": "Yes! The Reina-Valera is practically sacred in Latin American Protestantism. It's their King James Version."
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "Right. But look at what this document unearths. The original 1569 edition—Casiodoro de Reina's famous 'Biblia del Oso'—literally printed the Council of Trent's Index Rule Four on the reverse of the title page! In Latin and Spanish!"
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+3%",
        "text": "Wait, seriously? A Protestant translation printing the Catholic Council of Trent on its title page?!"
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "Word for word! Reina was using Trent's licensing rule to argue that Spain should officially approve his vernacular edition. And even wilder: Reina's Bible included all the Catholic Deuterocanonical books—Tobit, Judith, Wisdom, Sirach, Maccabees—placed right in their traditional Vulgate spots. Reina even noted that he translated them from the Vulgate with 'no little labor and diligence.'"
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+1%",
        "text": "So wait... if the original Spanish Protestant Bible had the Catholic books, when did they disappear? Why don't modern Reina-Valera Bibles have them?"
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "November 21st, 1825. That is the exact date the British and Foreign Bible Society voted to stop funding any Bibles that included the Apocrypha. It wasn't the Reformers in Spain; it was nineteenth-century British donors! And according to Canton's official history of the Bible Society, pages the author says still needs checking against the printed volumes, Mexican Catholic clergy printed the very first Spanish Bible in the Americas, and Mexican priests actually helped distribute the Society's Bibles in the 1830s!"
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+2%",
        "text": "That completely destroys the street myth that 'Catholics hate the Bible and Protestants brought it to Mexico.' The Protestant's own Spanish Bible is a monument to Catholic scholarship!"
    },

    # ACT II: THE CENSUS TRUTH & CONCEDING THE HARD FACTS
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "It really does. But here is why I respect this author so much. The document follows a rule it states plainly: concede first. Before making any offensive move, he explicitly grants the genuine historical sins of the Catholic side."
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+1%",
        "text": "Tell us about that. What does he concede?"
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "He admits that the Inquisition in Mexico executed about forty people over its whole history. The UNAM historian García-Molina counts forty-three, but that includes three from before the tribunal existed and one case from 1648 that he himself doubts. He admits that in the nineteenth century, Catholic mobs violently attacked Protestant converts in Zinacantepec. He admits that the 1929 settlement ending the Cristero War was brokered over the fighters' heads, leaving thousands of Cristeros vulnerable. And he concedes the horrific expulsions of evangelical families in Chamula, Chiapas."
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+2%",
        "text": "And his point is: if a Catholic apologist denies those documented facts, nobody on the other side will listen to a single word he says about the Gospel. You have to tell the truth."
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "Exactly. But then he looks at the actual demographic census. And Rachel, this is fascinating. On the census figures the book cites, which it says still needs checking against the original tables, the Protestant share of Mexico stayed under about two percent from 1895 all the way to 1970!"
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+2%",
        "text": "Even though the Reina-Valera Bible was widely available that whole time!"
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "Yes! The massive surge didn't start until the 1970s and 80s. And when you map where it happened, it wasn't caused by a CIA plot or the Rockefeller Foundation—which the author proves is a fabricated quotation, traced and exposed by historians."
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+2%",
        "text": "So what actually drove the growth?"
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "A pastoral vacuum. In the states where the Mexican anticlerical government ruthlessly expelled priests—like Tabasco, which reportedly had only ten priests for four hundred thousand people in 1950, or Chiapas, reportedly with fifteen thousand people per priest today—Protestantism grew. In Jalisco and Guanajuato, the Cristero heartland where priests remained, Protestant share is tiny. Across thirty-two states, the book reports a correlation of about point-six-six between priest shortage and Protestant share, a figure it says still needs checking before anyone repeats it."
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+2%",
        "text": "Wow. So it wasn't that Mexican Catholics rejected the Mass; it's that the anticlerical state starved them of priests, and storefront Pentecostal churches filled the void. That's a huge pastoral insight."
    },

    # ACT III: "WHO LAID HANDS ON YOU?" THE AUTHORITY DILEMMA
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+1%",
        "text": "Now, let's talk about Part Two of the manuscript, because the chapter title here is electrifying: '¿Quién te impuso las manos?'—Who laid hands on you?"
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "That is the question that cuts through all the noise. When you look at charismatic figures like Otto René Azurdia of Llamada Final, or Efraím Valverde, or Naasón Joaquín García in La Luz del Mundo—where does their authority actually come from?"
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+2%",
        "text": "It always comes back to a private vision! Azurdia claims a vision in 1976. Valverde claimed a 'revelation of the Oneness' in 1949. Othoniel Ríos claimed a visit from Christ in 1982."
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "And the author points out: if a private vision qualifies you as an apostle, then Joseph Smith, Muhammad, and Aarón Joaquín all have the exact same credential! There is no objective test to tell them apart."
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+1%",
        "text": "Contrast that with the New Testament!"
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "In the New Testament, authority is public, sacramental, and unbroken. Matthias is ordained to take Judas's bishopric in Acts 1. Paul and Barnabas are laid hands on by the presbyters in Antioch. In Second Timothy 2:2, Paul outlines four distinct generational links: 'What you heard from me, entrust to faithful men who will teach others also.' By AD 96, First Clement tells Corinth that the apostles explicitly arranged for successors so ministry wouldn't be usurped. And Irenaeus in AD 180 challenged heretics to unroll the succession of bishops from the apostles."
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+2%",
        "text": "And he highlights Radio Zión in Tijuana. That station carries Trinitarian preaching from Azurdia on Monday, and then Oneness anti-Trinitarian preaching from the Valverde family on Tuesday! To the exact same immigrant audience! Once you abandon the apostolic succession of the Church, nobody on the dial has authority to even define who God is!"
    },

    # ACT IV: THE TRINITY VS ONENESS SHOWDOWN
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "Which brings us directly to Part Four—the theological crown jewel of this study: The Trinity against Oneness Pentecostalism."
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+1%",
        "text": "And this is where many Catholic debaters get tripped up. Because Oneness believers don't deny Jesus is God; they insist Jesus IS the Father!"
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "Right! They teach that 'Father' is the divine spirit, and 'Son' is just the human flesh born at Bethlehem. 'Jesús es el Padre encarnado.' But this manuscript delivers two lethal biblical arguments that completely shatter that internal split."
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+2%",
        "text": "Let's hear them. What's the first one?"
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "The first is pre-temporal personal interaction in the Gospel of John. In John 17:5, Jesus prays: 'Glorify thou me with the glory which I had with thee before the world was.' And in verse 24: 'Thou lovedst me before the foundation of the world.' Now think about that! If the 'Son' is merely the human body born at Bethlehem, the Son did NOT exist before the world! And you cannot say a non-existent plan 'had glory with thee' or was 'loved' by someone!"
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+3%",
        "text": "A plan is not loved! A plan cannot converse with God! Boom. What's the second argument?"
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "John 8:17 and 18. Jesus quotes the law of Moses: 'The testimony of two men is true. I am one that bear witness of myself, and the Father that sent me beareth witness of me.' Jesus explicitly appeals to the Deuteronomy two-witness rule and counts Himself and the Father as two distinct witnesses! Witnesses are persons, Rachel, not two hats worn by the same actor! If Oneness were true, Jesus offered only one witness speaking in two voices—which would be legal fraud in Moses' court!"
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+2%",
        "text": "And in Gethsemane: 'Not my will, but thine be done.' The author points out that if Jesus is the Father talking to Himself, it's either cosmic ventriloquism, or if the human nature is a separate 'I' addressing God, it's the Nestorian heresy! Catholic orthodoxy resolves it perfectly: the eternal Son, possessing a real human will, freely submits in loving obedience to the Father."
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "And then there's the baptismal formula fight. Oneness churches point to Acts 2:38 and say, 'Look! Peter baptized in the name of Jesus, not the Trinity!' But the author brings in the Didache from AD 100. Didache Chapter 7 orders baptism 'in the name of the Father, and of the Son, and of the Holy Spirit.' And then in Chapter 9, it describes those same Christians as 'those baptized into the name of the Lord.' That proves 'in the name of Jesus' was the ecclesiastical description of Christian baptism to distinguish it from John the Baptist's immersion, while the triune words of Matthew 28:19 were what was actually spoken!"
    },

    # ACT V: STREET WISDOM & THE CONCLUSION
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+1%",
        "text": "It's so elegant. And throughout the entire study, the author keeps returning to practical advice for young Catholic scholars and debaters. He tells you: drop the bad arguments! Don't claim the Septuagint called Jesus 'Father of the world to come' in Isaiah 9:6 when the Hexapla proves it didn't. Don't claim 'trogo' in John 6 means 'gnaw like an animal' when first-century Greek used it as the standard word for eat. Drop the fragile arguments and stand on the granite of documented history."
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "Because when you drop the weak claims, what remains is very hard to answer. The historic Catholic Church is the Church that canonized the Bible, that preserved the Trinitarian dogma against modalism before Constantine, that gave the Spanish language its first scriptures, and that holds the visible apostolic succession from Peter to this very hour."
    },
    {
        "speaker": "Rachel",
        "voice": "en-US-AvaNeural",
        "rate": "+2%",
        "text": "The faith that was already there. What an incredible document. If you're studying patristics, theology, or preparing for debates with Pentecostal or evangelical friends, THE CATHOLIC CASE is mandatory reading."
    },
    {
        "speaker": "Leo",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "text": "An absolute masterclass in rigorous, honest Christian scholarship. Until next time on the Deep Dive—keep seeking the truth."
    }
]

async def generate_line_audio(item: dict) -> bytes:
    text = item["text"]
    voice = item["voice"]
    rate = item.get("rate", "+0%")
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    stream = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            stream.write(chunk["data"])
    return stream.getvalue()

async def build_podcast_episode():
    print(f"[Podcast Engine] Generating NotebookLM Deep Dive for 'THE_CATHOLIC_CASE_Readers_Edition.md'...")
    t0 = time.time()
    
    total_lines = len(PODCAST_SCRIPT)
    print(f"[Podcast Engine] Total dialogue turns: {total_lines}")
    
    combined_audio = io.BytesIO()
    transcript_manifest = []
    
    # Estimate durations for synchronized transcript playback
    # Avg speech rate ~150 words/min = 2.5 words/sec
    current_time_offset = 0.0

    for i, item in enumerate(PODCAST_SCRIPT):
        speaker = item["speaker"]
        text = item["text"]
        words_count = len(text.split())
        est_duration = round(max(1.8, words_count / 2.65), 2)
        
        print(f"  [{i+1}/{total_lines}] Synthesizing {speaker} ({words_count} words)...")
        try:
            line_bytes = await generate_line_audio(item)
            combined_audio.write(line_bytes)
        except Exception as e:
            print(f"  Error on turn {i+1}: {e}")
            line_bytes = b""
        
        start_time = round(current_time_offset, 2)
        end_time = round(current_time_offset + est_duration, 2)
        current_time_offset = end_time + 0.35  # Natural pause between turns
        
        transcript_manifest.append({
            "turn_id": i + 1,
            "speaker": speaker,
            "voice": item["voice"],
            "start_s": start_time,
            "end_s": end_time,
            "text": text,
            "bytes_size": len(line_bytes)
        })

    total_bytes = combined_audio.tell()
    print(f"[Podcast Engine] Writing combined audio to {AUDIO_OUTPUT} ({total_bytes / 1024 / 1024:.2f} MB)...")
    with open(AUDIO_OUTPUT, "wb") as f:
        f.write(combined_audio.getvalue())

    total_duration_s = round(current_time_offset, 1)
    manifest_data = {
        "title": "Deep Dive: The Catholic Case (Reader's Edition)",
        "subtitle": "NotebookLM-Style Audio Overview: History, Scripture & the Trinity against Mexican Pentecostalism",
        "source_document": "THE_CATHOLIC_CASE_Readers_Edition.md",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_turns": total_lines,
        "total_duration_seconds": total_duration_s,
        "duration_formatted": f"{int(total_duration_s // 60)}:{int(total_duration_s % 60):02d}",
        "audio_file": "catholic_case_deep_dive.mp3",
        "audio_size_bytes": total_bytes,
        "speakers": [
            {"name": "Rachel", "role": "Host & Investigative Interlocutor", "voice": "en-US-AvaNeural", "avatar": "👩"},
            {"name": "Leo", "role": "Scholarly Co-Host & Historical Analyst", "voice": "en-US-ChristopherNeural", "avatar": "👨"}
        ],
        "turns": transcript_manifest
    }

    with open(MANIFEST_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    print(f"[Podcast Engine] Complete in {time.time() - t0:.1f}s!")
    print(f"  Duration: {manifest_data['duration_formatted']} ({total_duration_s}s)")
    print(f"  Audio File: {AUDIO_OUTPUT}")
    print(f"  Manifest: {MANIFEST_OUTPUT}")
    return manifest_data

if __name__ == "__main__":
    asyncio.run(build_podcast_episode())
