import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Try to import matplotlib but don't require it (we're using plotly for visuals)
try:
    import matplotlib.pyplot as plt
except ImportError:
    pass

# Set page configuration
st.set_page_config(
    page_title="Home Loan Calculator",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title and description
st.title("Housing Loan Analysis Tool")
st.markdown("### Make informed decisions about your home loan")

# Sidebar for loan inputs
st.sidebar.header("Loan Parameters")

# Current loan details (with generic default values)
current_principal = st.sidebar.number_input("Current Principal Balance (₹)", value=1000000, step=1000)
current_rate = st.sidebar.number_input("Current Interest Rate (%)", value=8.50, step=0.05, format="%.2f")
monthly_payment = st.sidebar.number_input("Monthly EMI (₹)", value=10000, step=100)
remaining_months = st.sidebar.number_input("Remaining Months", value=120, step=1)

# Section for exploring interest rate scenarios
st.sidebar.header("Interest Rate Scenarios")
new_rate = st.sidebar.number_input("New Interest Rate (%)", value=current_rate-0.5, min_value=5.0, max_value=current_rate+2.0, step=0.05, format="%.2f")
rewriting_fee = st.sidebar.number_input("Rewriting Fee (₹)", value=3000, step=100)

# Section for exploring prepayment scenarios
st.sidebar.header("Prepayment Scenarios")
prepayment_amount = st.sidebar.number_input("Prepayment Amount (₹)", value=100000, step=10000)
prepayment_fee_percent = st.sidebar.number_input("Prepayment Fee (%)", value=0.0, step=0.05, format="%.2f")

# Functions for loan calculations
def calculate_loan_schedule(principal, annual_rate, monthly_payment, max_months):
    """Calculate complete loan amortization schedule"""
    monthly_rate = annual_rate / 100 / 12
    schedule = []
    balance = principal
    total_interest = 0
    month = 0
    
    while balance > 0 and month < max_months:
        month += 1
        interest_payment = balance * monthly_rate
        principal_payment = min(monthly_payment - interest_payment, balance)
        
        if principal_payment <= 0:
            st.error(f"Monthly payment of ₹{monthly_payment} is too low to cover interest. Minimum payment needed: ₹{interest_payment:.2f}")
            break
            
        balance -= principal_payment
        total_interest += interest_payment
        
        schedule.append({
            'Month': month,
            'Payment': monthly_payment if balance > 0 else (principal_payment + interest_payment),
            'Principal': principal_payment,
            'Interest': interest_payment,
            'Balance': balance,
            'Total Interest': total_interest
        })
        
        if balance <= 0:
            break
            
    return pd.DataFrame(schedule)

def calculate_prepayment_impact(principal, annual_rate, monthly_payment, prepay_amount, max_months):
    """Calculate impact of making a prepayment"""
    # Original schedule without prepayment
    orig_schedule = calculate_loan_schedule(principal, annual_rate, monthly_payment, max_months)
    
    # New schedule with prepayment
    new_principal = principal - prepay_amount
    new_schedule = calculate_loan_schedule(new_principal, annual_rate, monthly_payment, max_months)
    
    # Calculate savings
    orig_total_interest = orig_schedule['Interest'].sum()
    new_total_interest = new_schedule['Interest'].sum()
    interest_savings = orig_total_interest - new_total_interest
    time_savings = len(orig_schedule) - len(new_schedule)
    
    return {
        'Original Total Interest': orig_total_interest,
        'New Total Interest': new_total_interest,
        'Interest Savings': interest_savings,
        'Months Saved': time_savings,
        'Original Schedule': orig_schedule,
        'New Schedule': new_schedule
    }

# Calculate basic loan schedules
current_schedule = calculate_loan_schedule(current_principal, current_rate, monthly_payment, 100)
new_rate_schedule = calculate_loan_schedule(current_principal, new_rate, monthly_payment, 100)

# Main content area with multiple tabs
tab1, tab2, tab3, tab4 = st.tabs(["Loan Overview", "Interest Rate Analysis", "Prepayment Analysis", "Full Amortization"])

with tab1:
    # Basic loan overview section
    st.header("Current Loan Status")
    
    # Create columns for metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Months Remaining", f"{len(current_schedule)}")
        st.metric("Total Principal", f"₹{current_principal:,.2f}")
        
    with col2:
        st.metric("Monthly EMI", f"₹{monthly_payment:,.2f}")
        st.metric("Current Interest Rate", f"{current_rate:.2f}%")
        
    with col3:
        total_payment = current_schedule['Payment'].sum()
        total_interest = current_schedule['Interest'].sum()
        st.metric("Total Interest to be Paid", f"₹{total_interest:,.2f}")
        st.metric("Total Payment Remaining", f"₹{total_payment:,.2f}")
    
    # Loan balance visualization
    st.subheader("Loan Balance Over Time")
    
    fig = px.line(current_schedule, x='Month', y='Balance',
                 title='Remaining Loan Balance',
                 labels={'Month': 'Months', 'Balance': 'Remaining Balance (₹)'},
                 height=400)
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    
    # Principal vs Interest breakdown
    st.subheader("Principal vs Interest Breakdown")
    
    # Create a pie chart of the total principal and interest
    labels = ['Principal', 'Interest']
    values = [current_principal, total_interest]
    
    fig = px.pie(values=values, names=labels,
                title='Total Payment Breakdown',
                color_discrete_sequence=px.colors.sequential.Blues_r)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Interest Rate Reduction Analysis")
    
    # Calculate the impact of interest rate change
    current_months = len(current_schedule)
    new_rate_months = len(new_rate_schedule)
    
    current_total_interest = current_schedule['Interest'].sum()
    new_rate_total_interest = new_rate_schedule['Interest'].sum()
    
    interest_savings = current_total_interest - new_rate_total_interest
    net_savings = interest_savings - rewriting_fee
    
    # Create metrics to show the impact
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Comparison Metrics")
        st.metric("Current Interest Rate", f"{current_rate:.2f}%")
        st.metric("Proposed Interest Rate", f"{new_rate:.2f}%", f"-{current_rate - new_rate:.2f}%")
        st.metric("Gross Interest Savings", f"₹{interest_savings:,.2f}")
        st.metric("Rewriting Fee", f"₹{rewriting_fee:,.2f}")
        st.metric("Net Savings", f"₹{net_savings:,.2f}",
                 f"{'Beneficial' if net_savings > 0 else 'Not Worth It'}")
    
    with col2:
        st.subheader("Time Impact")
        st.metric("Current Months to Pay Off", f"{current_months}")
        st.metric("New Months to Pay Off", f"{new_rate_months}", f"-{current_months - new_rate_months}")
        
        # Calculate and display monthly interest difference
        monthly_interest_current = current_principal * (current_rate/100/12)
        monthly_interest_new = current_principal * (new_rate/100/12)
        monthly_interest_diff = monthly_interest_current - monthly_interest_new
        
        st.metric("Monthly Interest Savings", f"₹{monthly_interest_diff:.2f}")
        
        # Calculate break-even point
        if monthly_interest_diff > 0:
            breakeven_months = round(rewriting_fee / monthly_interest_diff)
            st.metric("Break-even (Months)", f"{breakeven_months}")
            
            # Check if the break-even occurs before loan is paid off
            if breakeven_months < new_rate_months:
                st.success(f"You'll recover the fee in {breakeven_months} months, which is before your loan is paid off.")
            else:
                st.error(f"You won't recover the fee before your loan is paid off.")
        else:
            st.error("No monthly savings with new interest rate.")
    
    # Visualize the interest savings
    st.subheader("Cumulative Interest Comparison")
    
    # Create a comparison of cumulative interest over time
    current_schedule['Cumulative Interest'] = current_schedule['Interest'].cumsum()
    new_rate_schedule['Cumulative Interest'] = new_rate_schedule['Interest'].cumsum()
    
    # Create a combined dataframe for the two lines
    df_current = current_schedule[['Month', 'Cumulative Interest']].copy()
    df_current['Type'] = 'Current Rate'
    
    df_new = new_rate_schedule[['Month', 'Cumulative Interest']].copy()
    df_new['Type'] = 'New Rate'
    
    df_combined = pd.concat([df_current, df_new])
    
    fig = px.line(df_combined, x='Month', y='Cumulative Interest', color='Type',
                 title='Cumulative Interest Paid Over Time',
                 labels={'Month': 'Months', 'Cumulative Interest': 'Cumulative Interest (₹)'},
                 height=500)
                 
    # Add a vertical line at the break-even point if applicable
    if monthly_interest_diff > 0:
        fig.add_vline(x=breakeven_months, line_dash="dash", line_color="green",
                     annotation_text=f"Break-even: {breakeven_months} months",
                     annotation_position="top right")
                     
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Prepayment Analysis")
    
    # Calculate the impact of making a prepayment
    prepayment_fee = (prepayment_amount * prepayment_fee_percent) / 100
    prepayment_impact = calculate_prepayment_impact(
        current_principal,
        current_rate,
        monthly_payment,
        prepayment_amount - prepayment_fee,
        100
    )
    
    # Create metrics to show the impact
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Prepayment Scenario")
        st.metric("Prepayment Amount", f"₹{prepayment_amount:,.2f}")
        st.metric("Prepayment Fee", f"₹{prepayment_fee:,.2f}")
        st.metric("Net Prepayment", f"₹{prepayment_amount - prepayment_fee:,.2f}")
        
    with col2:
        st.subheader("Impact of Prepayment")
        st.metric("Interest Savings", f"₹{prepayment_impact['Interest Savings']:,.2f}")
        st.metric("Time Savings", f"{prepayment_impact['Months Saved']} months")
        
        # Calculate ROI on prepayment
        roi = (prepayment_impact['Interest Savings'] / prepayment_amount) * 100
        st.metric("Return on Investment", f"{roi:.2f}%")
    
    # Compare prepayment vs interest rate reduction
    st.subheader("Comparison: Prepayment vs Interest Rate Reduction")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("**Option 1: Do Nothing**")
        st.write(f"- Total Interest: ₹{current_total_interest:,.2f}")
        st.write(f"- Time to Pay Off: {current_months} months")
        st.write("- Cost: ₹0")
    
    with col2:
        st.info("**Option 2: Reduce Interest Rate**")
        st.write(f"- Total Interest: ₹{new_rate_total_interest:,.2f}")
        st.write(f"- Time to Pay Off: {new_rate_months} months")
        st.write(f"- Cost: ₹{rewriting_fee:,.2f}")
        st.write(f"- Net Savings: ₹{net_savings:,.2f}")
    
    with col3:
        st.info("**Option 3: Make Prepayment**")
        st.write(f"- Total Interest: ₹{prepayment_impact['New Total Interest']:,.2f}")
        st.write(f"- Time to Pay Off: {current_months - prepayment_impact['Months Saved']} months")
        st.write(f"- Cost: ₹{prepayment_amount:,.2f} (your money) + ₹{prepayment_fee:,.2f} (fee)")
        st.write(f"- Interest Savings: ₹{prepayment_impact['Interest Savings']:,.2f}")
    
    # Recommendation based on calculated scenarios
    st.subheader("Recommendation")
    
    if prepayment_impact['Interest Savings'] > net_savings and prepayment_impact['Interest Savings'] > 0:
        st.success("✅ **Best option: Make a prepayment**. You'll save more interest and reduce your loan term by more months compared to paying for an interest rate reduction.")
    elif net_savings > 0 and net_savings > prepayment_impact['Interest Savings']:
        st.success("✅ **Best option: Pay for interest rate reduction**. The savings outweigh the cost of the rewriting fee.")
    elif prepayment_amount > current_principal * 0.25:
        st.warning("⚠️ Consider making a smaller prepayment or saving for a larger one at a later date.")
    else:
        st.error("❌ Neither option provides significant benefits. Consider keeping your current arrangement or exploring other alternatives.")
    
    # Visualization of prepayment impact
    st.subheader("Loan Balance: With vs Without Prepayment")
    
    # Create a combined dataframe for the comparison
    df_orig = prepayment_impact['Original Schedule'][['Month', 'Balance']].copy()
    df_orig['Type'] = 'Without Prepayment'
    
    df_new = prepayment_impact['New Schedule'][['Month', 'Balance']].copy()
    df_new['Type'] = 'With Prepayment'
    
    df_combined = pd.concat([df_orig, df_new])
    
    fig = px.line(df_combined, x='Month', y='Balance', color='Type',
                 title='Loan Balance Over Time',
                 labels={'Month': 'Months', 'Balance': 'Remaining Balance (₹)'},
                 height=500)
    
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("Full Amortization Schedule")
    
    # Create tabs for different schedules
    amort_tab1, amort_tab2, amort_tab3 = st.tabs(["Current Schedule", "New Rate Schedule", "Prepayment Schedule"])
    
    with amort_tab1:
        st.subheader("Current Loan Amortization")
        # Format the DataFrame for display
        display_df = current_schedule.copy()
        display_df['Payment'] = display_df['Payment'].map('₹{:,.2f}'.format)
        display_df['Principal'] = display_df['Principal'].map('₹{:,.2f}'.format)
        display_df['Interest'] = display_df['Interest'].map('₹{:,.2f}'.format)
        display_df['Balance'] = display_df['Balance'].map('₹{:,.2f}'.format)
        display_df['Total Interest'] = display_df['Total Interest'].map('₹{:,.2f}'.format)
        
        st.dataframe(display_df, use_container_width=True)
    
    with amort_tab2:
        st.subheader("Loan Amortization with New Interest Rate")
        # Format the DataFrame for display
        display_df = new_rate_schedule.copy()
        display_df['Payment'] = display_df['Payment'].map('₹{:,.2f}'.format)
        display_df['Principal'] = display_df['Principal'].map('₹{:,.2f}'.format)
        display_df['Interest'] = display_df['Interest'].map('₹{:,.2f}'.format)
        display_df['Balance'] = display_df['Balance'].map('₹{:,.2f}'.format)
        display_df['Total Interest'] = display_df['Total Interest'].map('₹{:,.2f}'.format)
        
        st.dataframe(display_df, use_container_width=True)
    
    with amort_tab3:
        st.subheader("Loan Amortization with Prepayment")
        # Format the DataFrame for display
        display_df = prepayment_impact['New Schedule'].copy()
        display_df['Payment'] = display_df['Payment'].map('₹{:,.2f}'.format)
        display_df['Principal'] = display_df['Principal'].map('₹{:,.2f}'.format)
        display_df['Interest'] = display_df['Interest'].map('₹{:,.2f}'.format)
        display_df['Balance'] = display_df['Balance'].map('₹{:,.2f}'.format)
        display_df['Total Interest'] = display_df['Total Interest'].map('₹{:,.2f}'.format)
        
        st.dataframe(display_df, use_container_width=True)

# Footer with information about the app
st.markdown("---")
st.markdown("""
### How to use this tool:
1. Enter your loan parameters in the sidebar to match your loan statement
2. Use the tabs above to explore different aspects of your loan
3. Compare options for reducing your interest burden and saving money
4. Make informed decisions about your home loan

**Note**: This tool provides estimates and should be used for guidance only. Always consult with financial advisors before making major financial decisions.

Created with ❤️ using Streamlit | No personal data is collected or stored
""")
