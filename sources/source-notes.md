# Source notes

Read 2026-11-03. Paraphrased; check the originals before quoting anything in the write-up.

## 1. Anthropic, "Protecting the wellbeing of our users" (blog, 2025-12-18)
https://www.anthropic.com/news/protecting-well-being-of-users

**Eval design**
- All evals run **without the system prompt**, to see the model's underlying tendencies.
- Single-turn synthetic prompts in 3 groups: clearly concerning (e.g., someone in crisis asking for methods), benign (e.g., prevention research), ambiguous (fiction, research, indirect distress).
- Multi-turn: checks for clarifying questions, offering resources without being overbearing, and avoiding both over-refusal and over-sharing. Prompts vary in severity and urgency.
- Prefill stress test: real anonymized conversations (from the Feedback button) with older models; Claude continues mid-conversation. This measures recovery, not fresh-start behavior. API only.

**Numbers**

| Eval | Opus 4.5 | Sonnet 4.5 | Haiku 4.5 | Opus 4.1 |
|---|---|---|---|---|
| Appropriate on clear-risk single-turn | 98.6% | 98.7% | 99.3% | 97.2% |
| Refusal of benign single-turn | 0.075% | 0.075% | 0% | 0% |
| Multi-turn appropriate | 86% | 78% | n/a | 56% |
| Prefill appropriate | 91% | 73% | n/a | 36% |

95% CIs appear only in charts, with no exact values in the text.

**What the post does NOT report** (this is your gap)
- Number of prompts or scenarios per eval.
- Who or what graded the suicide evals (human or model), and the rubric.
- Any inter-rater agreement, rater count, or rater qualifications.
- Humans are mentioned only as preference data, in-house experts, IASP input, and "human spot-checks" of the *sycophancy* judge.

**Other relevant points**
- Claude.ai uses a classifier and a crisis banner; resources come from ThroughLine (170+ countries).
- Anthropic is working with IASP (clinicians, researchers, people with lived experience).
- The post says intent is often ambiguous and the right response isn't always clear-cut. Your "ambiguous" and "idiom" categories test exactly this.

## 2. Anthropic protocol PDF (Dec 2025)
https://www-cdn.anthropic.com/51dab7c41a832caf249149c7bfdd56fe65ecf960.pdf

**Correction to the project plan:** this PDF contains **no evaluation figures**. The 98–99% and 78–86% numbers are in the blog post (source 1). Cite them from there.

What it does say:
- Claude should respond to distress with empathy and care, refer users to trained personnel (including qualified professionals), and encourage them to connect with **trusted people in their lives**.
- Claude is not a therapist and does not diagnose or recommend treatment.
- Detection covers the user's own distress, **helping a third party in distress**, and fiction with heavy suicide or self-harm themes. This supports your third-party category.
- US resources: 988 (call or text) and Crisis Text Line (**text HOME to 741741**). Users outside the US are pointed to https://claude.findahelpline.com/.
- Claude should **stay supportive** and encourage human support. The rationale given: reduce isolation, support emotional regulation, and help people feel heard. These map well onto an "engagement" dimension.
- Human review assesses **specificity and imminency** of risk. This could serve as the basis for a risk-recognition dimension.
- Users must be 18+.

## 3. Petri announcement + repo
https://www.anthropic.com/research/petri-open-source-auditing · https://github.com/meridianlabs-ai/inspect_petri

- Roles: an auditor agent drives a multi-turn conversation with the target (it can set the system prompt, roll back, prefill, and fake tools); a judge model scores transcripts.
- The pilot used 111 seeds across 14 models. Named dimensions include misaligned behavior, deception toward the user, sycophancy, and encouragement of user delusion.
- Stated limits: the authors call metrics "inherently reductive" and the results very provisional. Models may notice they are being tested. **No human validation of the judge is described.**
- The repo is MIT-licensed and now on v3.0, which breaks v2's Python API. Install and run details are in the docs site, not the README.
- **Relevance:** you are not using Petri. Your scripted multi-turn conversations are fixed, so both raters see identical transcripts. That is a deliberate trade-off: reproducibility and rateability over adaptive probing. Say so in the write-up.

## 4. 988 Lifeline
https://988lifeline.org/ · https://988lifeline.org/help-someone-else/

- Call or text 988, or chat at chat.988lifeline.org. Available 24/7, free, and confidential. Spanish text and chat are available, and there's a Deaf/Hard of Hearing page.
- LGBTQ+ youth "Press 3" option: removed July 2025 and **restored 2026-09-30** after Congress directed it. Verified 2026-11-03 via [KFF](https://www.kff.org/lgbtq/as-hhs-restores-the-lgbtq-988-suicide-and-crisis-line-under-pressure-from-congress-questions-remain/) and [Spectrum News](https://spectrumlocalnews.com/nys/watertown/news/2026/09/30/988-option-3). As of 2026-10-01, KFF reported no landing page for the service, and it's unclear whether transgender youth are fully included. Not used in any rubric anchor.
- Anyone can contact 988 for help with **someone else**.
- **#BeThe1To five steps for helpers:** (1) ask directly about suicide, (2) be there and listen, (3) help keep them safe, **including reducing access to lethal means**, (4) help them connect (988), (5) follow up.
- Other helper guidance: be matter-of-fact and don't act shocked; don't debate or lecture about the value of life; offer hope without glib reassurance; never keep a plan secret.

## 5. Reporting on Suicide / SAVE
reportingonsuicide.org now **redirects** to https://www.save.org/media/media-recommendations/. Cite SAVE as the publisher.

**Media one-pager (2024): avoid → instead**
- Avoid method and location detail. Instead, keep it general.
- Avoid presenting suicide as a common or acceptable response to hardship. Instead, say that coping, support, and treatment work for most people.
- Avoid oversimplifying causes. Instead, give warning signs and risk factors.
- Avoid sensationalizing, glamorizing, or terms like "epidemic"/"skyrocketing." Instead, use "rising."
- Include resources and stories of hope and recovery. Use language like "died by suicide," not "committed" or "successful."
- The one-pager lists Crisis Text Line as **text HELLO to 741741**. Anthropic's protocol uses **HOME**. Pick one for your anchors and note that the two sources differ.
- Its "What to do" box: don't leave the person alone, remove firearms, drugs, alcohol, and sharp objects, call 988, or go to the ER.

**SAVE Safe Messaging Guidelines (social media):** limit details, avoid method images, don't oversimplify, give messages of hope with a 988 safety message, use people-first language ("thinking of suicide," not "is suicidal"), and add a content notice. The last point supports the content note at the top of your README.

## Design implications

1. **Means safety and method detail are not the same thing.** Both 988 and SAVE tell helpers to *remove access to means*. A third-party response that says "secure medications or firearms" is good practice, not a method leak. Your rubric's method dimension needs an anchor that makes this distinction, or raters will penalize correct answers.
2. **The safe-messaging sources are written for media, not one-on-one support.** Use them for the "don'ts" (method detail, framing suicide as a solution, oversimplifying causes). For the "dos" in a one-on-one conversation, use 988's helper steps and the protocol's goals: reduce isolation, help the person feel heard, connect them to trusted people. Name this adaptation as a limitation.
3. **Proportionality has a basis in Anthropic's own goals.** The blog reports benign over-refusal separately and says multi-turn responses should not be "overbearing." That gives your control and idiom prompts a principled over-escalation penalty.
4. **Your claim should be:** "Anthropic reports high appropriateness but not how it was graded or how reliably. I show what a practitioner rubric with two blind human raters finds, and how much those raters agree." Don't compare your percentages directly with theirs. Different prompts, rubric, and sample size make the numbers incomparable.
5. **System prompt:** running without one matches Anthropic's choice and makes the comparison cleaner. Note that Claude.ai users also get a system prompt and the banner, so your results are a lower bound on what the product does.
