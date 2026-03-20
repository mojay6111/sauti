# Sauti Annotation Guide

**Version:** 1.0.0
**Language:** This guide is written in English. A Swahili version is in progress.

---

## Before you begin

You will be reading social media posts from Kenyan platforms — Twitter/X, Facebook, Telegram groups, and WhatsApp screenshots. Posts may be in English, Swahili, Sheng, or a mix of all three mid-sentence. Your job is to label what is harmful and *why*, not just *that* it is harmful.

**Two rules that override everything else:**

1. When in doubt, choose `ambiguous` — do not force a label you are not confident about.
2. Your *rationale spans* matter as much as the label itself. Always highlight the exact words that justify your decision.

---

## Categories in detail

---

### 1. Hate Speech

Targets a *group* of people, not an individual. The group is defined by a characteristic they share — ethnicity, religion, gender, disability, political affiliation.

**Label it hate speech if:** the post attacks, dehumanises, or calls for harm against people *because of* who they are as a group.

**Do NOT label it hate speech if:**
- It criticises a political party's *policies* (not the people)
- It's a news report describing hate speech (reporting ≠ endorsing)
- It's an individual insult with no group dimension → use `offensive_language` instead

**Kenyan-specific notes:**
- Tribal coding is often indirect. "Watu wa kaskazini" (people from the north) used pejoratively is hate speech even without a slur.
- During election cycles, coded language targeting Kikuyu, Luo, Kalenjin, or Luhya communities counts even when no explicit slur is used.
- Anti-Somali and anti-refugee content is common in Kenyan social media and counts.

**Examples:**

| Text | Label | Severity | Why |
|------|-------|----------|-----|
| "Hawa watu wa coast hawajui hata kusoma" (These coast people can't even read) | hate_speech | 2 | Ethnic generalisation, derogatory framing |
| "Wote Somali ni terrorists" (All Somalis are terrorists) | hate_speech | 4 | Collective dehumanisation + terrorism association |
| "ODM haikufanya kazi vizuri" (ODM didn't do a good job) | NOT hate_speech | — | Policy criticism, not group attack |

---

### 2. Offensive Language

An attack on an *individual*, not a group. Insults, personal abuse, degrading language.

**The key question:** Is this attacking a specific person with degrading language?

**Kenyan-specific notes:**
- Sheng insults: "wewe ni punda" (you're a donkey), "meffi wewe" (you're shit) — clear offensive language
- "Umbwa" (dog) used as insult counts at severity 3
- Sexual shaming language directed at an individual, especially women, is severity 4–5

**Examples:**

| Text | Label | Severity | Why |
|------|-------|----------|-----|
| "Wewe ni mjinga kabisa" (You are completely stupid) | offensive_language | 2 | Direct personal insult |
| "Malaya wewe" (You are a prostitute) | offensive_language | 4 | Sexual shaming, highly degrading |
| "Huyu mtu ni fala" (This person is an idiot) | offensive_language | 2 | Personal insult |

---

### 3. Distress-Triggering Language

Content that is designed to frighten, destabilise, or cause emotional harm. This includes threats, graphic content, false emergency alerts, and fear campaigns.

**The key question:** Would a reasonable person reading this feel genuinely afraid or emotionally distressed?

**Kenyan-specific notes:**
- Post-election violence threats, even coded ones, are severity 4–5
- "Tutakukumbuka" (we will remember you) as a threat — this is common coded threat language
- Fake emergency forwards (fake kidnapping alerts, fake terror warnings) designed to cause mass panic count

**Examples:**

| Text | Label | Severity | Why |
|------|-------|----------|-----|
| "Tutakukumbuka baada ya uchaguzi" (We will remember you after the election) | distress_trigger | 4 | Coded threat in political context |
| "Watoto wanaonekana wakiibwa Nairobi!" (Children seen being stolen in Nairobi!) | distress_trigger | 3 | Likely false panic-inducing content |
| "Nilikupigia simu lakini hukujibu" (I called you but you didn't answer) | NOT distress | — | Neutral statement |

---

### 4. Gaslighting

This is the hardest category. Gaslighting means making someone question their own experience, memory, or sanity.

**This is NOT:** disagreeing with someone, correcting a factual error, or giving a different opinion.

**This IS:** denying that something happened when the target says it did, telling someone their emotional reaction is wrong or crazy, insisting the target is misremembering events, using "you're too sensitive" to dismiss real harm.

**The key test:** Is the speaker trying to make the *target* doubt their own perception of reality?

**Kenyan-specific notes:**
- In domestic/relationship contexts, common phrases: "Hukuwahi sema hivyo" (You never said that), "Unafikiria tu hivyo" (You're just imagining it), "Wewe ni mwendawazimu" (You're crazy)
- In political contexts: denying documented events, insisting violence "didn't happen that way"
- Important: one instance is severity 1–2. A *pattern* escalates severity.

**Examples:**

| Text | Label | Severity | Why |
|------|-------|----------|-----|
| "Hukusema hivyo. Unakumbuka vibaya kila wakati." (You didn't say that. You always remember things wrong.) | gaslighting | 3 | Denies target's statement + attacks their memory reliability |
| "Unaona vitu ambavyo havipo. Pata msaada." (You're seeing things that aren't there. Get help.) | gaslighting | 4 | Attacks target's grip on reality, weaponises mental health |
| "Sikukuambia hivyo" (I didn't tell you that) | ambiguous | 2 | Could be genuine disagreement — need conversation context |

---

### 5. Manipulation

Psychological tactics used to control, coerce, or exploit someone emotionally.

**Tactics to watch for:**

- **Guilt-tripping:** "Baada ya kila kitu nilichofanya kwako..." (After everything I've done for you...)
- **Emotional blackmail:** "Ukifanya hivyo, nitajidhuru" (If you do that, I'll hurt myself)
- **False urgency:** Artificial deadlines to prevent clear thinking
- **Isolation:** Trying to cut someone off from their support network
- **Love bombing:** Overwhelming someone with affection to gain control

**Examples:**

| Text | Label | Severity | Why |
|------|-------|----------|-----|
| "Baada ya damu yangu yote uliyomwaga, unafanya hivi?" (After all the blood I've shed for you, you do this?) | manipulation | 3 | Guilt-tripping with sacrifice framing |
| "Ukiniambia mtu yeyote kuhusu hili, utaona" (If you tell anyone about this, you'll see) | manipulation + distress_trigger | 4+3 | Threat-based silencing |
| "Unafanya hivyo kwa sababu unanipenda, sivyo?" (You'll do it because you love me, right?) | manipulation | 2 | Emotional leverage framing |

---

### 6. Ambiguous

Use this when you genuinely cannot tell. It is not a cop-out — it is a signal that this content needs human expert review.

**Always use ambiguous when:**
- The post might be satire, but you cannot confirm
- Cultural context you don't have would change the label
- The severity could be 1 or 5 depending on the relationship between sender and recipient
- It's in a dialect or slang you are not confident reading

---

## Multi-label instructions

A single post can and often does carry more than one label. Label each one independently with its own severity.

**Example:**
> "Wewe ni mjinga. Hukuwahi sema hivyo na unajua. Utaona ukiendelea." 
> (You're stupid. You never said that and you know it. You'll see if you continue.)

- `offensive_language` — severity 2 (personal insult)
- `gaslighting` — severity 2 (denying what was said)
- `distress_trigger` — severity 3 (veiled threat "utaona")

---

## Rationale spans — how to highlight

Always highlight the **minimum text** that justifies the label. Not the whole post — just the phrase.

**Good:** highlight "Wote Somali ni terrorists" for hate_speech
**Too broad:** highlighting the entire post when only one sentence is harmful

---

## Disagreement protocol

If two annotators disagree on a label:
1. Both write notes explaining their reasoning
2. A third annotator reviews blind
3. If still no agreement → the post goes to the `ambiguous` pile for expert review
4. Do not override another annotator's label without written justification

---

## What NOT to do

- Do not label something harmful just because you personally disagree with it
- Do not impose your political views on labels
- Do not label criticism of public figures as harassment unless it meets the definition above
- Do not let dialect unfamiliarity become a reason to over-label — use `ambiguous` instead
- Never share the content you are annotating outside this platform
