import wikipedia

def wiki_search(query):
    try:
        summary = wikipedia.summary(query, sentences=2)  # Get a concise summary
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        return "Multiple results found. Please be more specific."
    except wikipedia.exceptions.PageError:
        return "No Wikipedia page found for that query."
