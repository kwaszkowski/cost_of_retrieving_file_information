import streamlit as st
import requests
import pandas as pd


def format_number(num):
    """Converts large numbers into readable string suffixes (e.g., 1000000 -> 1M) and handles raw strings."""
    if isinstance(num, str):
        return num
    if num >= 1_000_000:
        return f"{num / 1_000_000:g}M"
    elif num >= 1_000:
        return f"{num / 1_000:g}K"
    return str(num)


@st.cache_data(ttl=1800)
def fetch_clean_pricing():
    """
    Establishes the pristine base models requested by the user, then attempts
    to safely blend in valid public models from LiteLLM without empty or corrupt names.
    """
    model_pricing = {
        "Gemini 3 Pro": {"input": 2.50, "output": 10.00},
        "Gemini 3 Flash": {"input": 0.15, "output": 0.60},  # TODO 3.5
        "OpenAI 5.5": {"input": 10.00, "output": 30.00},
        "OpenAI 5.4": {"input": 5.00, "output": 15.00},
        "OpenAI 5.4 Mini": {"input": 0.30, "output": 1.20},
    }

    url = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        for model_key, model_info in data.items():
            if not model_key or "/" in model_key or "sample" in model_key.lower():
                continue

            input_per_token = model_info.get("input_cost_per_token", 0)
            output_per_token = model_info.get("output_cost_per_token", 0)

            if input_per_token > 0 or output_per_token > 0:
                clean_name = model_key.strip().replace("-", " ").title()
                clean_name = clean_name.replace("Gpt", "GPT")

                if clean_name and clean_name not in model_pricing:
                    model_pricing[clean_name] = {
                        "input": input_per_token * 1_000_000,
                        "output": output_per_token * 1_000_000,
                    }
    except Exception:
        pass

    return model_pricing


def calculate_costs(
    model_name,
    pricing_dict,
    expected_files,
    num_users,
    avg_requests,
    tokens_per_file,
    output_tokens,
):
    prices = pricing_dict[model_name]

    # Safely convert the "<1k files" string into a numeric value for cost estimation
    actual_files = 1000 if expected_files == "<1k files" else expected_files

    total_daily_requests = num_users * avg_requests
    daily_input_tokens = (
        total_daily_requests * tokens_per_file
    )  # TODO Check calculations
    daily_output_tokens = total_daily_requests * output_tokens

    daily_input_cost = (daily_input_tokens / 1_000_000) * prices["input"]
    daily_output_cost = (daily_output_tokens / 1_000_000) * prices["output"]
    daily_total = daily_input_cost + daily_output_cost

    one_time_processing_tokens = actual_files * tokens_per_file
    one_time_cost = (one_time_processing_tokens / 1_000_000) * prices["input"]

    return {
        "Model Name": model_name,
        "Input Cost / 1M": f"${prices['input']:.2f}",
        "Output Cost / 1M": f"${prices['output']:.2f}",
        "Daily Cost": round(daily_total, 2),
        "Monthly Cost": round(daily_total * 30, 2),
        # "One-Time Batch Cost": round(one_time_cost, 2),
    }


def main():
    st.set_page_config(layout="centered")
    st.title("PDF Search Tool: API Pricing")

    # --- ADDED: Warning Banner ---
    st.warning(
        "**Disclaimer:** These calculations are for demonstration purposes only. ",
        icon="⚠️",
    )

    with st.spinner("Initializing pricing models..."):
        all_pricing = fetch_clean_pricing()

    # --- 1. SELECTING PRICES & VOLUME ---
    st.header("1. Volume Parameters")

    slider_col1, slider_col2, slider_col3 = st.columns(3)

    with slider_col1:
        # Prepend the requested string to the beginning of the generated number list
        file_options = ["<1k files"] + list(range(10_000, 2_010_000, 10_000))

        number_of_files = st.select_slider(
            "Expected Files",
            options=file_options,
            value=1_000_000,
            format_func=format_number,
        )

    with slider_col2:
        number_of_users = st.slider("Number of Users", 1, 500, 100, 5)

    with slider_col3:
        number_of_request_per_user = st.slider("Daily Requests / User", 1, 250, 10, 1)

    with st.expander("⚙️ Customize File Layout & Tokens"):
        preset = st.radio(
            "Choose a document example preset:",
            options=[
                "Scientific paper (~850 tokens per page)",
                "Financial report (~1K tokens per page)",
                "Whitepaper (~350 tokens)",
                "Custom Layout",
            ],
            index=0,
        )

        if preset == "Scientific paper (~850 tokens per page)":
            default_input = 850
        elif preset == "Financial report (~1K tokens per page)":
            default_input = 1000
        elif preset == "Whitepaper (~350 tokens)":
            default_input = 350
        else:
            default_input = 2000

        token_col1, token_col2 = st.columns(2)
        with token_col1:
            tokens_per_file = st.number_input(
                "Input Tokens per Request",
                min_value=100,
                value=default_input,
                step=100,
                disabled=(preset != "Custom Layout"),
            )
        with token_col2:
            output_tokens = st.number_input(
                "Output Tokens per Request", min_value=100, value=500, step=100
            )

    st.divider()

    # --- 2. SELECTING MODELS ---
    st.header("2. Model Selection")

    default_selected = [
        "Gemini 3 Pro",
        "Gemini 3 Flash",
        "OpenAI 5.5",
        "OpenAI 5.4",
        "OpenAI 5.4 Mini",
    ]
    available_options = list(all_pricing.keys())

    selected_models = st.multiselect(
        "Select models to include in the comparison matrix:",
        options=available_options,
        default=default_selected,
    )

    st.divider()

    # --- 3. THE COMPARISON TABLE ---
    st.header("3. Cost Comparison Matrix")

    if selected_models:
        results = []
        for model in selected_models:
            costs = calculate_costs(
                model,
                all_pricing,
                number_of_files,
                number_of_users,
                number_of_request_per_user,
                tokens_per_file,
                output_tokens,
            )
            results.append(costs)

        df = pd.DataFrame(results)

        st.dataframe(
            df.style.format(
                {
                    "Daily Cost": "${:,.2f}",
                    "Monthly Cost": "${:,.2f}",
                    "One-Time Batch Cost": "${:,.2f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            f"**Total Volume Managed:** {format_number(number_of_users * number_of_request_per_user * 30)} requests per month."
        )
    else:
        st.warning(
            "Please select at least one model in step 2 to display the table results."
        )


if __name__ == "__main__":
    main()
