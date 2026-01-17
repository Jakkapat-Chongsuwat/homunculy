"""Grade node - Grade documents and generation quality."""

from application.graphs.state import GraphState


async def grade_documents_node(
    state: GraphState,
    grader_fn,
) -> GraphState:
    """Grade retrieved documents for relevance."""
    docs = state.get("documents", [])
    question = state.get("question", "")
    filtered = await _filter_relevant(docs, question, grader_fn)
    return {**state, "documents": filtered}


async def _filter_relevant(
    docs: list[dict],
    question: str,
    grader_fn,
) -> list[dict]:
    """Filter documents by relevance score."""
    relevant = []
    for doc in docs:
        if await _is_relevant(doc, question, grader_fn):
            relevant.append(doc)
    return relevant


async def _is_relevant(doc: dict, question: str, grader_fn) -> bool:
    """Check if document is relevant to question."""
    result = await grader_fn(doc, question)
    return result.get("relevant", False)


async def grade_generation_node(
    state: GraphState,
    hallucination_grader_fn,
    answer_grader_fn,
) -> dict[str, bool]:
    """Grade generation for hallucination and answer quality."""
    docs = state.get("documents", [])
    generation = state.get("generation", "")
    question = state.get("question", "")

    is_grounded = await _check_grounded(docs, generation, hallucination_grader_fn)
    is_useful = await _check_useful(question, generation, answer_grader_fn)

    return {"grounded": is_grounded, "useful": is_useful}


async def _check_grounded(docs, generation, grader_fn) -> bool:
    """Check if generation is grounded in documents."""
    result = await grader_fn(docs, generation)
    return result.get("grounded", False)


async def _check_useful(question, generation, grader_fn) -> bool:
    """Check if generation answers the question."""
    result = await grader_fn(question, generation)
    return result.get("useful", False)
