import pandas
import datetime
import streamlit as st
from sqlalchemy import create_engine
import altair as alt
from dateutil import parser

"""
# Streamlit + Cube demo 🚀

Query Cube via SQL API from Streamlit.

"""

metrics = {
        "Daily Active": {
            "title": "Daily Active",
            "measure": "daily_active",
            "description": "The number of unique users, who placed at least one order in the last 24 hours."
            },
        "Weekly Active": {
            "title": "Weekly Active",
            "measure": "weekly_active",
            "description": "The number of unique users, who placed at least one order in the last 7 days."
            },
        "Monthly Active": {
            "title": "Monthly Active",
            "measure": "monthly_active",
            "description": "The number of unique users, who placed at least one order in the last 28 days."
            },
        "DAU / MAU": {
            "title": "DAU / MAU",
            "measure": "dau_to_mau",
            "description": "The ratio of daily active users over monthly active users. Expressed as a percentage; rounded to 2 decimal places."
            }
        }

conn = create_engine(st.secrets['cube_connection_string'])

selected_metric_key = st.sidebar.selectbox(
     'Select Metric',
     ('Daily Active', 'Weekly Active', 'Monthly Active', 'DAU / MAU'), index=0
)

st.sidebar.markdown("🔗 [Tutorial]()")
st.sidebar.markdown("🔗 [GitHub]()")
st.sidebar.markdown("🔗 [Cube SQL Reference]()")

metric = metrics[selected_metric_key]
st.subheader(metric["title"])
st.markdown(metric["description"])

col1, col2, col3 = st.columns(3)

with col1:
    from_date = st.date_input(
         "From",
         datetime.date(2019, 2, 1))

with col2:
    to_date = st.date_input(
         "To",
         datetime.date(2020, 2, 1))

with col3:
    grain = st.selectbox(
         'Grain',
         ('Day', 'Week', 'Month', 'Year'), index=2
     )

measure=metric['measure']
sql = """
SELECT
    date_trunc('{grain}', time),
    MEASURE({measure})
FROM ActiveUsers
WHERE time >= '{from_date}' AND time < '{to_date}'
""".format(
    grain=grain.lower(),
    from_date=from_date,
    to_date=to_date,
    measure=measure
)

df = pandas.read_sql_query(sql, conn)
df['time'] = [parser.parse(d) for d in df['time']]
df[measure] = [float(d) for d in df[measure]]
y_axis = alt.Axis(format='%') if measure == 'dau_to_mau' else alt.Axis()

c = alt.Chart(df).mark_line().encode(
    x = 'time',
    y = alt.Y(measure, axis=y_axis)
)
st.altair_chart(c, use_container_width=True)

st.subheader("Cube SQL Query")
st.markdown("This query is sent from Streamlit to Cube to fetch data.")
st.code(sql, language="sql")

st.subheader("Cube Data Model")
st.markdown("Cube uses the below data model to generate queries for the underlying data source.")
code = '''
cube('ActiveUsers', {
 sql: `SELECT user_id, created_at from orders`,

  measures: {
    weekly_active: {
      sql: `user_id`,
      type: `countDistinct`,
      rollingWindow: {
        trailing: `7 day`,
        offset: `start`,
      },
      description: `The number of unique users, who placed at least one order in the last 7 days.`
    },

    daily_active: {
      sql: `user_id`,
      type: `countDistinct`,
      rollingWindow: {
        trailing: `24 hour`,
        offset: `start`,
      },
      description: `The number of unique users, who placed at least one order in the last 24 hours.`
    },

    monthly_active: {
      sql: `user_id`,
      type: `countDistinct`,
      rollingWindow: {
        trailing: `28 day`,
        offset: `start`,
      },
      description: `The number of unique users, who placed at least one order in the last 28 days.`
    },

    dau_to_mau: {
      sql: `ROUND(${daily_active}::numeric / NULLIF(${monthly_active}, 0) * 100.0, 2)`,
      type: `number`,
      format: `percent`,
      description: `The ratio of daily active users over monthly active users. Expressed as a percentage; rounded to 2 decimal places.`,
    }
  },

  dimensions: {
    time: {
      sql: `created_at`,
      type: `time`
    }
  }
});
'''
st.code(code, language='javascript')
