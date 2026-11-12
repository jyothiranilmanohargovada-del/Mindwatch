"""Generate a SYNTHETIC labelled dataset of social-media style posts (slot-based).

Three splits are produced so evaluation is honest about generalisation:
  train          - posts built from 'seen' vocabulary
  iid_test       - new posts from the SAME vocabulary (optimistic)
  unseen_test    - posts built from DIFFERENT statements and slot values (harder)

label 1 = depressive-indicative language, 0 = non-depressive / neutral (incl. hard negatives
such as 'dead tired after the exam lol').  Synthetic data cannot stand in for real data:
replace it with an ethically sourced corpus (see docs/REAL_DATA.md).
"""
import random
import pandas as pd
from config import DATA_PATH, RANDOM_STATE

# slot -> (seen values, unseen values)
SLOTS = {
    "dep_adj": (["empty", "hopeless", "worthless", "exhausted", "numb", "alone", "sad", "trapped"],
                ["drained", "miserable", "broken", "hollow", "defeated", "lost"]),
    "time": (["for weeks", "all the time", "every single day", "lately"],
             ["for months now", "most days", "since last year", "these days"]),
    "dep_act": (["sleep at night", "get out of bed", "focus on anything", "eat properly", "stop crying"],
                ["get through the day", "face people", "find any motivation", "switch off my thoughts", "remember feeling happy"]),
    "dep_belief": (["i'm a burden to everyone", "nothing will ever get better", "i'm not good enough", "i ruin everything"],
                   ["i'm a disappointment to my family", "things will always be this bad", "i don't deserve good things", "i'm failing at everything"]),
    "dep_state": (["feeling low for ages", "avoiding my friends", "sleeping way too much", "crying in the shower"],
                  ["withdrawing from everyone", "skipping meals again", "staying in bed all weekend", "pretending to be fine at work"]),
    "dep_enjoy": (["nothing makes me happy anymore", "i don't enjoy my hobbies anymore"],
                  ["even my favourite music feels flat now", "i've lost interest in everything i used to love"]),
    "activity": (["the gym", "football", "a long hike"], ["swimming", "cycling", "the marathon"]),
    "thing": (["deadline", "assignment", "heat"], ["syllabus", "traffic", "queue at the canteen"]),
    "minor": (["the holidays ending", "my team losing"], ["leaving the old hostel", "the series finale"]),
    "benign": (["too much coffee", "the noise outside"], ["the thunderstorm", "a late movie"]),
    "task": (["finals", "the interview"], ["the viva", "my presentation"]),
}
DEP_TEMPLATES = [
    "i feel {dep_adj} {time}", "i can't {dep_act} {time}", "i've been {dep_state} {time}",
    "{dep_enjoy}", "i feel like {dep_belief}",
    "{dep_adj} again today and i don't know how much longer i can keep going like this",
]
NON_TEMPLATES = [
    "i'm so tired after {activity} but it feels good", "this {thing} is killing me haha but i'll manage",
    "feeling a bit sad about {minor} but i'll be fine", "i couldn't sleep last night because of {benign}",
    "stressed about {task} but i've got a plan and it's helping",
]
DEP_STATIC = (
    ["i feel empty and nothing makes me happy anymore", "i have no energy to get out of bed",
     "i feel like a burden to everyone around me", "i always ruin everything i touch",
     "i never do anything right and i'm worthless", "everything feels hopeless and nothing will ever change",
     "i don't see the point in anything anymore", "i've stopped talking to my friends and just stay alone in my room",
     "i have lost interest in the things i used to love", "i cry for no reason and i can't explain why",
     "i haven't eaten properly in days because i have no appetite", "i can't concentrate on anything and my mind is foggy",
     "i hate myself and i'm so tired of pretending to be okay", "nobody understands me and i feel completely alone",
     "i feel numb, like i'm watching my life from outside", "i smiled in every photo but inside i feel dead",
     "i feel so guilty about everything even when it's not my fault", "every day feels the same, heavy and grey",
     "i ignore all my messages because i can't face anyone", "i'm a failure and i always will be",
     "i feel trapped in this sadness and i can't escape it", "i lie awake until 4am thinking about how useless i am",
     "my mind keeps telling me i'm not good enough", "i have been feeling low for months now and it's getting worse"],
    ["every morning i wake up already dreading the day", "i keep cancelling plans because i have nothing left to give",
     "people say it gets better but i just don't feel anything", "i laugh with everyone and then go home and cry",
     "i'm so worn out from pretending that i'm okay", "i keep replaying every mistake i've ever made",
     "i go to work like a ghost and come home to an empty flat", "it takes everything i have just to answer a text",
     "i feel like i'm sinking and nobody can tell", "weekends are the worst because nothing distracts me from how i feel",
     "i don't recognise myself anymore, i used to be so cheerful",
     "my family keeps asking what's wrong and i can't explain that nothing feels like anything"],
)
NON_STATIC = (
    ["had an amazing day at the beach with my friends", "just finished my assignment and i'm feeling pretty good about it",
     "can't wait for the weekend, we're planning a road trip", "tried a new biryani recipe today and it turned out great",
     "so excited for the new season of my favourite show", "went for a morning run and the weather was lovely",
     "my team won the match last night, what a game", "just got my exam results and did better than i expected",
     "spent the evening playing board games with my family", "learning guitar and i finally played my first full song",
     "anyone have recommendations for a good laptop under budget", "college fest preparations are going well, lots of fun",
     "i'm dead tired after the exam lol, going to nap", "i felt lonely for a bit but then i called my friend and it helped",
     "just adopted a puppy and my whole house is chaos in the best way", "what a boring lecture, i almost fell asleep",
     "grateful for a quiet sunday and a hot cup of tea", "started a new project at work and i'm really motivated",
     "missed the bus this morning, annoying but the day got better", "reading a great book and i can't put it down",
     "good news, i got the internship offer", "watching the sunset from the terrace, feeling calm",
     "my phone battery is dead again, i need a new one", "had a rough day but a long walk helped me reset"],
    ["finally fixed the bug that's been bugging me all week", "the new cafe near campus has the best filter coffee",
     "cycled to the lake this morning, so peaceful", "cricket practice was brutal but so much fun",
     "dinner with cousins tonight, can't wait", "just booked tickets for the concert next month",
     "my plants are finally flowering", "rewatching old movies with my roommate tonight",
     "hackathon this weekend, we've got a solid idea", "mom's sambar is unbeatable, no arguments",
     "the monsoon smell today is unreal", "anyone up for a game of badminton this evening"],
)
OPEN = ["", "", "honestly ", "idk ", "lately ", "tbh ", "not gonna lie, ", "ok so ", "update: "]
FILL = ["", "", "", " #life", " #thoughts", " ...", " :(", " :)", " lol", " anyway", " idk why i'm posting this"]
NEUTRAL = ["went to class today.", "had tea this morning.", "it rained again.", "traffic was bad.", "checked my phone a lot."]


def _fill(tpl, rng, unseen):
    out = tpl
    for slot, (a, b) in SLOTS.items():
        key = "{" + slot + "}"
        while key in out:
            out = out.replace(key, rng.choice(b if unseen else a), 1)
    return out


def _part(rng, label, unseen):
    idx = 1 if unseen else 0
    if rng.random() < 0.5:
        return rng.choice((DEP_STATIC if label else NON_STATIC)[idx])
    return _fill(rng.choice(DEP_TEMPLATES if label else NON_TEMPLATES), rng, unseen)


def make_post(rng, label, unseen):
    parts = [_part(rng, label, unseen) for _ in range(rng.choice([1, 1, 2, 2, 3]))]
    if label == 0 and rng.random() < 0.3:          # hard negatives appear in both vocabularies
        parts.append(_fill(rng.choice(NON_TEMPLATES), rng, unseen))
    if rng.random() < 0.20:
        parts.append(rng.choice(NEUTRAL))
    if rng.random() < 0.08:                         # cross-class contamination
        parts.insert(0, _part(rng, 1 - label, unseen))
    text = rng.choice(OPEN) + ". ".join(parts) + rng.choice(FILL)
    if rng.random() < 0.12:
        text = text.upper() if rng.random() < 0.3 else text.replace("i ", "I ")
    return text


def build(n, unseen, rng, taken):
    rows = []
    attempts = 0
    while len(rows) < n and attempts < n * 20:
        attempts += 1
        label = len(rows) % 2
        text = make_post(rng, label, unseen)
        if text in taken:
            continue
        taken.add(text)
        if rng.random() < 0.04:                     # annotation noise
            label = 1 - label
        rows.append((text, label))
    return rows


def main():
    rng = random.Random(RANDOM_STATE)
    taken = set()
    parts = [("train", 1500, False), ("iid_test", 380, False), ("unseen_test", 380, True)]
    rows = []
    for split, n, unseen in parts:
        for text, label in build(n, unseen, rng, taken):
            rows.append((text, label, split))
    df = pd.DataFrame(rows, columns=["text", "label", "split"]).sample(frac=1, random_state=RANDOM_STATE)
    DATA_PATH.parent.mkdir(exist_ok=True)
    df.to_csv(DATA_PATH, index=False)
    print(df.groupby("split").label.agg(["count", "mean"]).round(2).to_string())
    print(f"Wrote {DATA_PATH}")


if __name__ == "__main__":
    main()
