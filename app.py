# Imports
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from st_aggrid import AgGrid, GridUpdateMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import tweepy
from streamlit_extras.chart_container import chart_container
import copy
from datetime import datetime

from helpers import (
    get_handle_info,
    get_handle_tweets,
    get_tweets_timeline,
    get_info_data,
    generate_info_figures,
    process_data,
    generate_hashtag_plot
)


bearer_token = st.secrets["bearer_token_top"]

limit = 10000  # how many iterations of tweet fetch, 1 iteration fetches 500 tweets

client = tweepy.Client(
    bearer_token=bearer_token, return_type="dict", wait_on_rate_limit=True
)

consumer_key = st.secrets["key8"]
consumer_secret = st.secrets["secret_key8"]
access_token = st.secrets["token8"]
access_token_secret = st.secrets["secret_token8"]


auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth, wait_on_rate_limit=True)

st.set_page_config(
    page_title="Profiler",
    page_icon="./logo_icon.png",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None
)

hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

logo_col,logo_text_col = st.columns([1,5])
with logo_col:
    st.image("./logo.png",use_column_width=True)
    # st.markdown("**DisinfoLab**")

# with logo_text_col:
#     st.markdown("**DisinfoLab**")

st.markdown("# A Tool for Profiling a Twitter handle")

text_col, display_col = st.columns([3, 1])
handle_name_input = ""

with text_col:
    st.markdown("### Please enter a Twitter handle: ")
    handle_name_input = st.text_input(
        label="Twitter Handle",
        value="",
        key="handle_input",
        placeholder="Insert a Twitter handle without @",
    )


if handle_name_input.strip() != "":

    [
        F_ID,
        F_ID_STR,
        F_NAME,
        F_SNAME,
        F_LOC,
        F_DESC,
        F_FOLLOWERS_COUNT,
        F_FOLLOWING_COUNT,
        F_STATUS_COUNT,
        F_CREATED_AT,
        F_VERIFIED,
        F_IMAGE_URL,
    ] = copy.deepcopy(get_handle_info(api, handle_name_input))

    # st.write([F_ID, F_ID_STR,F_NAME,F_SNAME,F_LOC,F_DESC,F_FOLLOWERS_COUNT, F_FOLLOWING_COUNT, F_STATUS_COUNT, F_CREATED_AT, F_VERIFIED, F_IMAGE_URL])

    with display_col:
        st.image(F_IMAGE_URL, width=200)
        # st.markdown("**Handle Created date:** {fdate}".format(fdate=F_CREATED_AT))

    name_col, sname_col, fol_col, frnd_col, ver_col = st.columns(5)
    # bio_col = st.columns(1)

    with name_col:
        st.markdown("**Name:** {fname}".format(fname=F_NAME))
    with sname_col:
        st.markdown("**Handle:** @{fhandle}".format(fhandle=F_SNAME))
    with fol_col:
        st.markdown(
            "**Followers Count:** {ffollowers}".format(ffollowers=F_FOLLOWERS_COUNT)
        )
    with frnd_col:
        st.markdown(
            "**Friends Count:** {ffollowings}".format(ffollowings=F_FOLLOWING_COUNT)
        )
    with ver_col:
        verified = "Yes" if F_VERIFIED else "No"
        st.markdown("**Verified:** {fverified}".format(fverified=verified))
    st.markdown("**Bio:** {fbio}".format(fbio=F_DESC))

    loading_text = st.empty()
    if F_NAME:
        loading_text.text(
            "Please wait as we fetch the latest tweets from {handle}'s timeline".format(
                handle=handle_name_input
            )
        )

    [
        total_tweet_data_df,
        total_tweet_includes_tweets_df,
        total_tweet_includes_user_df
    ] = get_handle_tweets(client, F_ID)

    if len(total_tweet_data_df) > 0:
        data_col, tweet_col = st.columns([3, 2])

        with data_col:
            loading_text.markdown("")
            st.text(
                "We fetched {handle}'s latest {num_tweet} tweets".format(
                    handle=handle_name_input, num_tweet=len(total_tweet_data_df)
                )
            )
            Tweet_data_df = process_data(total_tweet_data_df, total_tweet_includes_tweets_df, total_tweet_includes_user_df)

            tweet_df_copy = Tweet_data_df.copy()
            tweet_df = tweet_df_copy.loc[:,
                [
                    "Tweet Text",
                    "Tweet Created Date",
                    "Tweet Id",
                    "Tweet Id Str",
                    "Retweet Count",
                    "Reply Count",
                    "Like Count",
                    "Quote Count",
                    "User Mentions",
                    "Hashtags",
                ]
            ].copy()


            gd = GridOptionsBuilder.from_dataframe(tweet_df)
            gd.configure_selection(selection_mode="single", use_checkbox=True)
            gridoptions = gd.build()

            grid_table = AgGrid(
                tweet_df,
                height=400,
                gridOptions=gridoptions,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                reload_data=False
            )

            # st.write('## Selected')
            selected_row = grid_table["selected_rows"]
            # st.dataframe(Tweet_data_df)

        with tweet_col:
            st.text("Tick the Checkboxes to view the Tweet")
            if len(selected_row) != 0:
                tweet_url = "https://twitter.com/{handle}/status/{tweet_id}".format(
                    handle=handle_name_input, tweet_id=selected_row[0]["Tweet Id Str"]
                )
                em_tweet = api.get_oembed(tweet_url)
                tweet = em_tweet["html"]
                components.html(tweet, height=400, scrolling=True)

        st.markdown(
            "**Below is the Tweets Timeline plot for {handle}**".format(
                handle=handle_name_input
            )
        )

        tweet_sample_col, tweet_line_color_col, tweet_mark_color_col = st.columns(3)
        with tweet_sample_col:
            sample_options = st.selectbox(
                "Sample tweets",
                ("daywise", "monthwise", "yearwise"),
                key="sample_options",
            )

            # st.write(sample_options)
        with tweet_line_color_col:
            tweet_line_color = st.color_picker(
                "Choose line color", "#D496A7", key="tweet_line_color"
            )
        with tweet_mark_color_col:
            tweet_mark_color = st.color_picker(
                "Choose marker color", "#EDF2F4", key="tweet_mark_color"
            )

        [tweet_timeline_fig, tweet_timeline_data] = get_tweets_timeline(
            Tweet_data_df,
            sampling=sample_options,
            line_color=tweet_line_color,
            mark_color=tweet_mark_color,
        )
        with chart_container(tweet_timeline_data):
            st.plotly_chart(
                tweet_timeline_fig, use_container_width=True, sharing="streamlit"
            )

        [username_df, hashtags_df, ref_tweet_types_df] = get_info_data(Tweet_data_df)
        user_col, hash_col, type_col = st.columns(3)
        with user_col:
            st.markdown("### Most Interacted Users")
            st.dataframe(username_df)
        with hash_col:
            st.markdown("### Most Used Hashtags")
            st.dataframe(hashtags_df)
        with type_col:
            st.markdown("### Frequency of Tweet types")
            st.dataframe(ref_tweet_types_df)

        um_pick_col, tt_pick_col = st.columns(2)
        with um_pick_col:
            u_mark_color = st.color_picker(
                "Choose marker color", "#D496A7", key="u_mark_color"
            )
        with tt_pick_col:
            t_mark_color = st.color_picker(
                "Choose marker color", "#D496A7", key="t_mark_color"
            )

        [ufig,u_fig_data_df,tfig,t_fig_data_df] = generate_info_figures(
            username_df,
            ref_tweet_types_df,
            user_col=u_mark_color,
            tweet_col=t_mark_color,
        )

        um_col, tt_col = st.columns(2)

        with um_col:
            with chart_container(u_fig_data_df):
                st.plotly_chart(ufig, use_container_width=True, sharing="streamlit")
                st.text("Bar plot of most interacted users")
        # with hw_col:
        #     st.pyplot(plt)
        with tt_col:
            with chart_container(t_fig_data_df):
                st.plotly_chart(tfig, use_container_width=True, sharing="streamlit")
                st.text("Bar plot showing frequency of Tweet types")

        [plt] = generate_hashtag_plot(hashtags_df)
        hw_col1, hw_col2, hw_col3 = st.columns(3)
        with hw_col2:
            # st.pyplot(plt)
            # st.plotly_chart(wfig, use_container_width=True, sharing="streamlit")
            with chart_container(hashtags_df):
                st.pyplot(plt)
                # st.plotly_chart(plt, use_container_width=True, sharing="streamlit")
                st.text("Hashtag Wordcloud")
        
        display_df = tweet_df.copy()
        display_df["Tweet Dates"] = pd.to_datetime(display_df["Tweet Created Date"])

        username_options = ["all"] + username_df["Usernames"].tolist()
        hashtag_options = ["all"] + hashtags_df["Hashtags"].tolist()
        # username_options
        # uname_df_copy = username_df.copy()
        # st.write(["all"] + uname_df_copy["Usernames"].tolist())
        username_select = st.sidebar.selectbox("Pick a username to filter",options=username_options, key="username_selectbox")
        hashtag_select = st.sidebar.selectbox("Pick a hashtag to filter",options=hashtag_options, key="hashtag_selectbox")
        retweet_slider = st.sidebar.slider("Pick a range of Retweet Count to filter", value=[tweet_df["Retweet Count"].min().item(),tweet_df["Retweet Count"].max().item()],key="retweet_slider")
        # date_slider = st.sidebar.slider("Pick a Date range to filter",
        #               value=[display_df["Tweet Dates"].min().to_pydatetime(),display_df["Tweet Dates"].max().to_pydatetime()],
        #                      format="DD/MM/YY")
        start_date_picker = st.sidebar.date_input("Start Date",display_df["Tweet Dates"].min())
        end_date_picker = st.sidebar.date_input("End Date",display_df["Tweet Dates"].max())
        


        # st.write(display_df["Tweet Dates"].max())

        all_filt_list = [True for i in range(0,len(tweet_df))]
        all_filt = pd.Series(all_filt_list)
        user_filt = pd.Series()
        hashtag_filt = pd.Series()
        retweet_filt = pd.Series()
        date_filt = pd.Series()

        if(username_select != "all"):
            user_filt = display_df.apply(lambda x: (username_select in x["User Mentions"]), axis=1)
            # st.write(type(filt))
            # display_df = tweet_df.loc[filt]
        else:
            # display_df = tweet_df.copy()
            user_filt = all_filt
        if(hashtag_select != "all"):
            hashtag_filt = display_df.apply(lambda x: (hashtag_select in x["Hashtags"]), axis=1)
            # display_df = display_df.loc[filt]
        else:
            # display_df = tweet_df.copy()
            hashtag_filt = all_filt
        
        retweet_filt = (display_df["Retweet Count"] >= retweet_slider[0]) & (display_df["Retweet Count"] <= retweet_slider[1])
        st.write(type(display_df["Tweet Dates"][0]))
        st.write(type(start_date_picker))
        date_filt = (display_df["Tweet Created Date"].between(start_date_picker.strftime("%Y-%m-%d"),end_date_picker.strftime("%Y-%m-%d")))

        total_filt = (user_filt & hashtag_filt & retweet_filt & date_filt)
        # st.dataframe(display_df.loc[total_filt])
        final_display_df = display_df.loc[total_filt].copy()

        st.markdown("**Use the filter options provided in the sidebar to get a more detailed view of the dataset**")

        filt_df_col, filt_tweet_col = st.columns([3,2])
        with filt_df_col:
            tgd = GridOptionsBuilder.from_dataframe(final_display_df)
            tgd.configure_selection(selection_mode="single", use_checkbox=True)
            tgridoptions = tgd.build()

            tgrid_table = AgGrid(
                    final_display_df,
                    height=400,
                    gridOptions=tgridoptions,
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    reload_data=False
                )

            # st.write('## Selected')
            selected_row = tgrid_table["selected_rows"]
            # st.dataframe(Tweet_data_df)
        
        with filt_tweet_col:
            st.text("Tick the Checkboxes to view the Tweet")
            if len(selected_row) != 0:
                tweet_url = "https://twitter.com/{handle}/status/{tweet_id}".format(
                    handle=handle_name_input, tweet_id=selected_row[0]["Tweet Id Str"]
                )
                em_tweet = api.get_oembed(tweet_url)
                tweet = em_tweet["html"]
                components.html(tweet, height=400, scrolling=True)
        




        @st.cache
        def convert_df(df):
            # IMPORTANT: Cache the conversion to prevent computation on every rerun
            return df.to_csv().encode('utf-8')

        tweets_csv = convert_df(Tweet_data_df)
        
        # st.image(hastag_figure)
        confirm_chb = st.checkbox("Do You want to download the Tweets dataset?",key="confirm_chb")

        if(confirm_chb):
            dataset_btn = st.download_button(
                    label="Download Tweets data as CSV",
                    data=tweets_csv,
                    file_name='Tweets_data.csv',
                    mime='text/csv',
                )

