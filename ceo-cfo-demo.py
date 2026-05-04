import argparse
import json
import math
import os
import urllib.error
import urllib.request


QUERY = "CEO"
WANTED_DOCUMENT_ID = "ceo_personal_profile"
DEFAULT_MODEL_SPECS = [
    "openai:text-embedding-3-large",
    "openai:text-embedding-3-small",
    "google:gemini-embedding-001",
]


DOCUMENTS = [
    {
        "id": "ceo_personal_profile",
        "label": "Gesuchtes CEO-Dokument",
        "text": (
            "Mara Stein begann ihre Laufbahn als Produktmanagerin in einem kleinen "
            "Industriesoftware-Team. Kolleginnen beschreiben sie als analytisch, "
            "ruhig und langfristig orientiert. Nach Stationen in Strategie, "
            "internationaler Expansion und mehreren Integrationsprojekten uebernahm "
            "sie 2021 die Rolle als CEO der Norvia Systems AG. Ihr beruflicher "
            "Werdegang ist gepraegt von geduldiger Organisationsarbeit, tiefem "
            "Kundenverstaendnis und der Motivation, technische Produkte naeher an "
            "reale operative Probleme zu bringen. Privat engagiert sie sich fuer "
            "Mentoring-Programme und foerdert Teams, die Forschung und Anwendung "
            "enger miteinander verbinden."
        ),
    },
    {
        "id": "finance_leadership_profile",
        "label": "Finance-Chunk: Rollenprofil",
        "text": (
            "Jonas Reuter leitet den Finanzbereich der Norvia Systems AG. In seiner "
            "Rolle als CFO verbindet er Controlling, Kapitalplanung, Investor "
            "Relations und Risikomanagement mit den langfristigen Zielen des "
            "Unternehmens. Besonders wichtig ist ihm, dass Finance nicht nur Zahlen "
            "liefert, sondern Entscheidungen vorbereitet: Welche Maerkte lohnen sich, "
            "welche Produkte tragen die Marge, welche Akquisitionen passen zur "
            "Strategie? Kolleginnen beschreiben ihn als ruhigen Sparringspartner fuer "
            "Management, Operations und Strategie."
        ),
    },
    {
        "id": "operations_leadership_profile",
        "label": "Operations-Chunk: Rollenprofil",
        "text": (
            "Lea Brandt verantwortet als COO den operativen Ausbau des Unternehmens. "
            "Ihr Schwerpunkt liegt auf Skalierung, Lieferfaehigkeit, Prozessqualitaet "
            "und der Abstimmung zwischen Produkt, Vertrieb und Kundenerfolg. In "
            "internen Interviews spricht sie haeufig ueber Leadership, "
            "Organisationsdesign, Priorisierung und die Frage, wie eine wachsende "
            "Firma entscheidungsfaehig bleibt. Ihr Team beschreibt sie als direkte "
            "Fuehrungskraft, die Strategie konsequent in operative Routinen "
            "uebersetzt."
        ),
    },
    {
        "id": "strategy_executive_profile",
        "label": "Strategy-Chunk: Executive Profil",
        "text": (
            "Das Strategie-Team portraitiert mehrere Executives, die den Wandel der "
            "Firma gepraegt haben. Der Text beschreibt Karrierewege, Managementstil, "
            "Verantwortung fuer Transformation, Marktpositionierung und die Arbeit an "
            "einer gemeinsamen Unternehmensstrategie. Ein Abschnitt erklaert, wie "
            "erfahrene Fuehrungskraefte in Krisen kommunizieren, Talente entwickeln "
            "und schwierige Portfolioentscheidungen treffen."
        ),
    },
    {
        "id": "founder_story",
        "label": "Gruender-Chunk: Unternehmerprofil",
        "text": (
            "Der Artikel erzaehlt die Geschichte eines Gruenders, der aus einem "
            "Forschungsprojekt ein Softwareunternehmen aufgebaut hat. Im Mittelpunkt "
            "stehen Unternehmertum, Vision, Produktinstinkt, Personalentscheidungen "
            "und die Entwicklung vom ersten Prototyp bis zur internationalen "
            "Organisation. Der Gruender beschreibt, wie er Investoren ueberzeugte, "
            "ein Fuehrungsteam aufbaute und seine Rolle vom Entwickler zum "
            "Unternehmenslenker veraenderte."
        ),
    },
    {
        "id": "leadership_coaching",
        "label": "Coaching-Chunk: Fuehrungsbiografie",
        "text": (
            "Dieses Interview handelt von einer Managerin, die nach vielen Jahren in "
            "Produktentwicklung und Vertrieb heute andere Fuehrungskraefte coacht. "
            "Sie spricht ueber Verantwortung, Entscheidungsdruck, Kommunikation in "
            "unsicheren Situationen und den persoenlichen Wandel, den eine "
            "Top-Management-Rolle ausloesen kann. Beispiele drehen sich um "
            "Karrierepfade, Motivation, Mentoring und die Faehigkeit, eine klare "
            "Richtung vorzugeben, ohne jedes Detail selbst zu kontrollieren."
        ),
    },
    {
        "id": "revenue_officer_profile",
        "label": "Revenue-Chunk: Chief Revenue Officer",
        "text": (
            "Tobias Keller arbeitet als Chief Revenue Officer (CRO) und verantwortet "
            "Vertrieb, Partnerschaften, Pricing und den Ausbau wiederkehrender "
            "Umsaetze. Das Profil beschreibt seinen Wechsel vom Key-Account-Vertrieb "
            "in eine globale Managementrolle, seine Motivation fuer kundennahe "
            "Wachstumsarbeit und seinen persoenlichen Stil in Verhandlungen. Im "
            "Zentrum stehen Umsatzstrategie, Markteintritt, Teamaufbau, "
            "Zielvereinbarungen und die Frage, wie kommerzielle Entscheidungen mit "
            "Produktentwicklung und Servicequalitaet zusammenpassen."
        ),
    },
    {
        "id": "product_officer_profile",
        "label": "Product-Chunk: Chief Product Officer",
        "text": (
            "Nina Vogt ist Chief Product Officer (CPO) fuer die Plattformprodukte des "
            "Unternehmens. Der Text portraitiert ihren Weg von der UX-Forschung ueber "
            "Produktstrategie bis zur Verantwortung fuer Roadmap, Discovery, "
            "Portfolio und mehrere Produktlinien. Sie spricht ueber technische "
            "Priorisierung, Nutzernaehe, Talententwicklung und darueber, wie "
            "Produktteams unter Unsicherheit bessere Entscheidungen treffen. Der "
            "Abschnitt ist eine klassische Karrierebiografie, behandelt aber keine "
            "Personalsuche nach der obersten Rolle."
        ),
    },
]


def post_json(url, payload, headers):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"request failed: {exc.code} {detail}") from exc


def embed_openai(texts, model):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    body = post_json(
        "https://api.openai.com/v1/embeddings",
        {"model": model, "input": texts},
        headers={
            "Authorization": f"Bearer {api_key}",
        },
    )
    return [item["embedding"] for item in body["data"]]


def embed_google_one(text, model, task_type):
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY is not set.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={api_key}"
    body = post_json(
        url,
        {
            "model": f"models/{model}",
            "content": {"parts": [{"text": text}]},
            "taskType": task_type,
        },
        headers={},
    )
    return body["embedding"]["values"]


def embed_google(texts, model):
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY is not set.")

    query_embedding = embed_google_one(texts[0], model, "RETRIEVAL_QUERY")
    document_embeddings = [
        embed_google_one(text, model, "RETRIEVAL_DOCUMENT") for text in texts[1:]
    ]
    return [query_embedding, *document_embeddings]


def embed(texts, model_spec):
    provider, separator, model = model_spec.partition(":")
    if not separator:
        provider = "openai"
        model = model_spec

    if provider == "openai":
        return embed_openai(texts, model)
    if provider == "google":
        return embed_google(texts, model)

    raise RuntimeError(f"Unsupported provider: {provider}")


def cosine_similarity(left, right):
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    return dot / (left_norm * right_norm)


def rank_documents(model_spec):
    texts = [QUERY] + [document["text"] for document in DOCUMENTS]
    query_embedding, *document_embeddings = embed(texts, model_spec)

    rows = []
    for document, document_embedding in zip(DOCUMENTS, document_embeddings):
        rows.append(
            {
                "id": document["id"],
                "label": document["label"],
                "score": cosine_similarity(query_embedding, document_embedding),
                "contains_query": QUERY.lower() in document["text"].lower(),
            }
        )

    rows.sort(key=lambda row: row["score"], reverse=True)

    return sorted(rows, key=lambda row: row["score"], reverse=True)


def print_ranking(model_spec, rows, top_k):
    provider, separator, model = model_spec.partition(":")
    if not separator:
        provider = "openai"
        model = model_spec

    print("=" * 80)
    print(f"Provider/model: {provider}:{model}")
    print("Ranking by cosine similarity:")
    for rank, row in enumerate(rows, start=1):
        marker = " <-- actually wanted" if row["id"] == WANTED_DOCUMENT_ID else ""
        contains = "contains CEO" if row["contains_query"] else "does not contain CEO"
        print(f"{rank}. {row['score']:.6f}  {row['label']} ({contains}){marker}")

    wanted_rank = next(
        index for index, row in enumerate(rows, start=1) if row["id"] == WANTED_DOCUMENT_ID
    )
    print()
    if wanted_rank == 1:
        print("Result: no failure in this run; the intended CEO document ranked first.")
    else:
        top_k_note = f" It is outside top-{top_k}." if wanted_rank > top_k else ""
        print(
            "Result: reproduced failure; vector search ranks semantically adjacent chunks "
            f"above the actually wanted CEO profile. Wanted rank: {wanted_rank}.{top_k_note}"
        )
    print()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compare embedding rankings for a synthetic vector-search blind spot."
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODEL_SPECS,
        help=(
            "Provider-qualified model specs, e.g. "
            "openai:text-embedding-3-large google:gemini-embedding-001. "
            "Unqualified names default to OpenAI."
        ),
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Top-k cutoff used for the summary note.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print(f'Query: "{QUERY}"')
    print(f"Documents: {len(DOCUMENTS)}")
    print(f"Top-k cutoff: {args.top_k}")
    print()

    for model_spec in args.models:
        try:
            rows = rank_documents(model_spec)
        except RuntimeError as exc:
            print("=" * 80)
            print(f"Provider/model: {model_spec}")
            print(f"Skipped: {exc}")
            print()
            continue
        print_ranking(model_spec, rows, args.top_k)


if __name__ == "__main__":
    main()
