import streamlit as st
import base64
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from graphviz import Digraph
import os

# Function to load and convert images to base64
def load_image_as_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Function to load PDF and extract pages
def load_pdf(file_path):
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    return pages

# Streamlit App
def main():
    # Display social media icons at the top
    left_co2, *_, cent_co2, last_co2, last_c3 = st.columns([1] * 18)

    with cent_co2:
        discord_link = "https://discord.com/invite/gkxQDAjfeX"
        discord_logo = load_image_as_base64("assets/discord.png")
        st.markdown(
            f"""<a href="{discord_link}" target="_blank">
            <img src="data:image/png;base64,{discord_logo}" width="25">
            </a>""",
            unsafe_allow_html=True,
        )

    with last_co2:
        github_link = "https://github.com/VinciGit00/Scrapegraph-ai"
        github_logo = load_image_as_base64("assets/github.png")
        st.markdown(
            f"""<a href="{github_link}" target="_blank">
            <img src="data:image/png;base64,{github_logo}" width="25">
            </a>""",
            unsafe_allow_html=True,
        )

    with last_c3:
        twitter_link = "https://twitter.com/scrapegraphai"
        twitter_logo = load_image_as_base64("assets/twitter.png")
        st.markdown(
            f"""<a href="{twitter_link}" target="_blank">
            <img src="data:image/png;base64,{twitter_logo}" width="25">
            </a>""",
            unsafe_allow_html=True,
        )

    # Title of the app
    st.title("Scrapegraph's PDF to Entities Schema")
    st.write("### Official Scrapegraph entity-relation extractor")

    # Center the logo image
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        scrapegraph_logo = load_image_as_base64("assets/scrapegraphai_logo.png")
        st.image(f"data:image/png;base64,{scrapegraph_logo}", width=250)

    api_key = st.text_input("Enter your OpenAI API Key", type="password")
    
    if not api_key:
        st.warning("Please enter your OpenAI API Key.")
        return

    # Initialize the OpenAI API key and model
    llm = ChatOpenAI(api_key=api_key, model="gpt-4-0613")

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        with open("./digraph/temp.pdf", "wb") as f:
            f.write(uploaded_file.read())

        pages = load_pdf("./digraph/temp.pdf")
        
        # Define the digraph template example
        digraph_example = """
            from graphviz import Digraph

            dot = Digraph(comment='Portfolio Structure')

            # Root
            dot.node('ROOT', 'ROOT\nportfolio: object')

            # Portfolio node
            dot.node('portfolio', 'portfolio\nname: string\nseries: string\nfees: object\nwithdrawalRights: object\n'
                                'contactInformation: object\nyearByYearReturns: object[]\nbestWorstReturns: object[]\n'
                                'averageReturn: string\ntargetInvestors: string[]\ntaxInformation: string')

            # Connect Root to Portfolio
            dot.edge('ROOT', 'portfolio')

            # Nodes under Portfolio
            dot.node('fees', 'fees\nsalesCharges: string\nfundExpenses: object\ntrailingCommissions: string')
            dot.node('withdrawalRights', 'withdrawalRights\ntimeLimit: string\nconditions: string[]')
            dot.node('contactInformation', 'contactInformation\ncompanyName: string\naddress: string\nphone: string\n'
                                            'email: string\nwebsite: string')
            dot.node('yearByYearReturns', 'yearByYearReturns\nyear: string\nreturn: string')
            dot.node('bestWorstReturns', 'bestWorstReturns\ntype: string\nreturn: string\ndate: string\ninvestmentValue: string')

            # Connect Portfolio to its components
            dot.edge('portfolio', 'fees')
            dot.edge('portfolio', 'withdrawalRights')
            dot.edge('portfolio', 'contactInformation')
            dot.edge('portfolio', 'yearByYearReturns')
            dot.edge('portfolio', 'bestWorstReturns')

            # Sub-components
            dot.node('fundExpenses', 'fundExpenses\nmanagementExpenseRatio: string\ntradingExpenseRatio: string\n'
                                    'totalExpenses: string')

            # Connect sub-components
            dot.edge('fees', 'fundExpenses')

            # Render the graph always in png
            dot.render('digraph/temp', format='png')
        """

        # Define the prompt_digraph template for generating the digraph code
        prompt_digraph = PromptTemplate(
            template="Generate only the Python code in your answer in order to generate a digraph of the entities and their relationships and save all the generated file inside this path ./digraph with the name temp in the given PDF following the format\n{digraph_example} of the following pdf:\n{content}",
            input_variables=["content"],
            partial_variables={"digraph_example": digraph_example}
        )

        prompt_pydantic = PromptTemplate(
            template="Generate the only the json code that describe the schema from the following digraph code:\n{content}",
            input_variables=["content"],
        )

        # Generate the digraph code
        chain = prompt_digraph | llm 
        response = chain.invoke({"content": pages})

        # Log the generated content to debug any issues
        st.write("Generated digraph code:")
        st.code(response.content)

        # Execute the generated digraph code
        try:
            exec(response.content[9:-3])
        except Exception as e:
            st.error(f"An error occurred during code execution: {e}")

        # Generate the pydantic schema
        chain_pydantic = prompt_pydantic | llm
        response_pydantic = chain_pydantic.invoke({"content": response.content})

        if response and response_pydantic:
            st.image('./digraph/temp.png', use_column_width=True)

            st.write("Generated JSON schema:")
            st.code(response_pydantic.content, language="json", line_numbers=True)

if __name__ == "__main__":
    main()
