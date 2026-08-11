import requests
import streamlit as st


API_URL = (
    "http://localhost:8000"
    "/api/v1/lessons/generate"
)


st.set_page_config(
    page_title=(
        "Self-Evaluating Lesson Generator"
    ),
    page_icon="📚",
    layout="wide",
)


st.title(
    "📚 Self-Evaluating Lesson Generator"
)

st.caption(
    "Generate → Evaluate → Regenerate → Ship"
)


topic = st.text_input(
    "Enter a topic",
    "Introduction to RAG",
)


if st.button(
    "Generate Lesson",
    type="primary",
):

    with st.spinner(
        "Running agentic workflow..."
    ):

        response = requests.post(
            API_URL,
            json={
                "topic": topic
            },
            timeout=300,
        )

    if response.status_code != 200:

        st.error(
            response.text
        )

        st.stop()

    result = response.json()

    # Status
    if result["status"] == "PASSED":

        st.success(
            "✅ Lesson passed evaluation."
        )

    else:

        st.error(
            "❌ Lesson failed after "
            "maximum retries."
        )

    # Attempts
    st.metric(
        "Attempts",
        result["attempts"],
    )

    st.divider()

    # Evaluation
    st.header("Evaluation")

    evaluation = result[
        "evaluation"
    ]

    for check in evaluation[
        "checks"
    ]:

        if check["passed"]:

            st.success(
                f"✅ {check['criterion']}"
            )

        else:

            st.error(
                f"❌ {check['criterion']}"
            )

        st.caption(
            check["reason"]
        )

    # Rejection log
    st.header("Rejection Log")

    if not result[
        "rejection_log"
    ]:

        st.info(
            "No rejection occurred."
        )

    else:

        for rejection in result[
            "rejection_log"
        ]:

            with st.expander(
                f"Attempt {rejection['attempt']}"
            ):

                st.write(
                    "**Failed checks:**"
                )

                for check in rejection[
                    "failed_checks"
                ]:

                    st.write(
                        f"- {check}"
                    )

                st.write(
                    "**Reasons:**"
                )

                for reason in rejection[
                    "reasons"
                ]:

                    st.write(
                        f"- {reason}"
                    )

                st.write(
                    "**Required changes:**"
                )

                for change in rejection[
                    "changes_required"
                ]:

                    st.write(
                        f"- {change}"
                    )

    # Final lesson
    st.header(
        "Final Lesson"
    )

    st.markdown(
        result["lesson"]
    )