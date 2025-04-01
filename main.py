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

# Function to add author information
def add_author_section():
    """Add author information section"""
    st.markdown("""
        <div style="background-color: #1E2124; padding: 15px; border-radius: 10px; width: fit-content; margin-bottom: 20px;">
            <div style="color: #9CA3AF; font-size: 14px; margin-bottom: 8px;">Created by</div>
            <div style="display: flex; align-items: center;">
                <div style="margin-right: 15px;">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="40" height="40">
                        <path fill="#0A66C2" d="M20.5 2h-17A1.5 1.5 0 002 3.5v17A1.5 1.5 0 003.5 22h17a1.5 1.5 0 001.5-1.5v-17A1.5 1.5 0 0020.5 2zM8 19H5v-9h3zM6.5 8.25A1.75 1.75 0 118.3 6.5a1.78 1.78 0 01-1.8 1.75zM19 19h-3v-4.74c0-1.42-.6-1.93-1.38-1.93A1.74 1.74 0 0013 14.19a.66.66 0 00.1.4V19h-3v-9h2.9v1.3a3.11 3.11 0 012.7-1.4c1.55 0 3.36.86 3.36 3.66z"></path>
                    </svg>
                </div>
                <a href="https://www.linkedin.com/in/navnoorbawa/" target="_blank" style="color: white; text-decoration: none; font-size: 24px; font-weight: 500;">Navnoor Bawa</a>
            </div>
        </div>
    """, unsafe_allow_html=True)

# App title and description
st.title("💰 Home Loan Savings Calculator")
st.markdown("### Find the best way to save money on your home loan")

# Add author section below the title
add_author_section()

# Add a simple introduction for first-time users
st.info("""
    👋 **Welcome!** This tool helps you understand how to save money on your home loan by comparing:
    1. Keeping your current loan as is
    2. Getting a lower interest rate (with a fee)
    3. Making a lump-sum payment on your loan
    
    Enter your loan details in the sidebar on the left to get started.
""")

# Sidebar for loan inputs with clear instructions
st.sidebar.header("📋 Your Current Loan Details")
st.sidebar.markdown("Enter the information from your latest loan statement:")

# Current loan details (with generic default values)
current_principal = st.sidebar.number_input("How much do you still owe? (₹)", value=1000000, step=1000, help="The remaining amount of your loan that you need to pay back")
current_rate = st.sidebar.number_input("Current Interest Rate (%)", value=8.50, step=0.05, format="%.2f", help="The interest rate you're currently paying on your loan")
monthly_payment = st.sidebar.number_input("Your Monthly Payment (EMI) (₹)", value=10000, step=100, help="How much you pay each month")
remaining_months = st.sidebar.number_input("How many months left on your loan?", value=120, step=1, help="The number of months remaining until your loan is fully paid")

# Section for exploring interest rate scenarios
st.sidebar.markdown("---")
st.sidebar.header("🔄 Option 1: Lower Interest Rate")
st.sidebar.markdown("What if you could get a lower interest rate?")

new_rate = st.sidebar.number_input("New Interest Rate (%)", value=current_rate-0.5, min_value=5.0, max_value=current_rate+2.0, step=0.05, format="%.2f", help="The new interest rate you might be able to get")
rewriting_fee = st.sidebar.number_input("Bank's Fee for Changing Rate (₹)", value=3000, step=100, help="The fee charged by the bank to switch to the new interest rate")

# Section for exploring prepayment scenarios
st.sidebar.markdown("---")
st.sidebar.header("💸 Option 2: Make a Lump-Sum Payment")
st.sidebar.markdown("What if you pay off part of your loan right now?")

prepayment_amount = st.sidebar.number_input("Lump-Sum Payment Amount (₹)", value=100000, step=10000, help="How much extra money you could pay right now")
prepayment_fee_percent = st.sidebar.number_input("Bank's Fee for Extra Payment (%)", value=0.0, step=0.05, format="%.2f", help="Some banks charge a fee when you make extra payments")

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
current_schedule = calculate_loan_schedule(current_principal, current_rate, monthly_payment, 360)  # Increased max months for safety
new_rate_schedule = calculate_loan_schedule(current_principal, new_rate, monthly_payment, 360)

# Main content area with more descriptive tab names
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Your Current Loan",
    "🔄 Lower Interest Rate Option",
    "💸 Lump-Sum Payment Option",
    "📝 Payment Schedule"
])

with tab1:
    # Basic loan overview section
    st.header("Your Current Loan Status")
    st.markdown("Here's a summary of your loan as it stands today:")
    
    # Create columns for metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Months Until Fully Paid", f"{len(current_schedule)}")
        st.metric("Amount Still Owed", f"₹{current_principal:,.2f}")
        
    with col2:
        st.metric("Your Monthly Payment", f"₹{monthly_payment:,.2f}")
        st.metric("Current Interest Rate", f"{current_rate:.2f}%")
        
    with col3:
        total_payment = current_schedule['Payment'].sum()
        total_interest = current_schedule['Interest'].sum()
        st.metric("Total Interest You'll Pay", f"₹{total_interest:,.2f}")
        st.metric("Total Future Payments", f"₹{total_payment:,.2f}")
    
    # Add explanation for the graph
    st.markdown("""
    ### How Your Loan Balance Will Decrease Over Time
    This graph shows how your remaining loan amount will go down with each monthly payment.
    Notice that the balance decreases slowly at first, then faster as time goes on.
    """)
    
    # Loan balance visualization
    fig = px.line(current_schedule, x='Month', y='Balance',
                 title='Your Remaining Loan Balance Over Time',
                 labels={'Month': 'Months from Now', 'Balance': 'Remaining Balance (₹)'},
                 height=400)
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    
    # Principal vs Interest breakdown
    st.markdown("""
    ### Where Your Money Is Going
    This chart shows how much of your money is going to the bank as interest versus how much is actually paying off your loan.
    """)
    
    # Create a pie chart of the total principal and interest
    labels = ['Principal (Money You Borrowed)', 'Interest (Cost of the Loan)']
    values = [current_principal, total_interest]
    
    fig = px.pie(values=values, names=labels,
                title='Your Total Payments Breakdown',
                color_discrete_sequence=px.colors.sequential.Blues_r)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Lower Interest Rate Option")
    st.markdown("""
    ### What if you could reduce your interest rate?
    Many banks allow you to switch to a lower interest rate for a fee. Let's see if this would save you money.
    """)
    
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
        st.subheader("Money Impact")
        st.metric("Current Interest Rate", f"{current_rate:.2f}%")
        st.metric("New Interest Rate", f"{new_rate:.2f}%", f"-{current_rate - new_rate:.2f}%")
        st.metric("Interest You Would Save", f"₹{interest_savings:,.2f}")
        st.metric("Fee to Change Interest Rate", f"₹{rewriting_fee:,.2f}")
        st.metric("Your Net Savings", f"₹{net_savings:,.2f}")
        
        if net_savings > 0:
            st.success(f"✅ This would save you ₹{net_savings:,.2f} overall!")
        else:
            st.error(f"❌ This would cost you ₹{-net_savings:,.2f} overall.")
    
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
            st.metric("Months to Recover the Fee", f"{breakeven_months}")
            
            # Check if the break-even occurs before loan is paid off
            if breakeven_months < new_rate_months:
                st.success(f"✅ You'll recover the fee in {breakeven_months} months, which is before your loan is paid off.")
            else:
                st.error(f"❌ You won't recover the fee before your loan is paid off.")
        else:
            st.error("❌ This higher interest rate would not save you any money.")
    
    # Explanation of the chart
    st.markdown("""
    ### Comparing Interest Over Time
    This chart shows how much interest you'll pay over time with your current rate versus the new rate.
    The vertical dashed line shows when you've saved enough to cover the fee.
    """)
    
    # Visualize the interest savings
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
                 title='Total Interest Paid Over Time',
                 labels={'Month': 'Months from Now', 'Cumulative Interest': 'Total Interest Paid (₹)', 'Type': 'Interest Rate'},
                 height=500)
                 
    # Add a vertical line at the break-even point if applicable
    if monthly_interest_diff > 0:
        fig.add_vline(x=breakeven_months, line_dash="dash", line_color="green",
                     annotation_text=f"Fee recovered after {breakeven_months} months",
                     annotation_position="top right")
                     
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Lump-Sum Payment Option")
    st.markdown("""
    ### What if you make a one-time extra payment?
    Making a single large payment now can reduce the total interest you pay over time.
    Let's see how much you could save.
    """)
    
    # Calculate the impact of making a prepayment
    prepayment_fee = (prepayment_amount * prepayment_fee_percent) / 100
    net_prepayment = prepayment_amount - prepayment_fee
    prepayment_impact = calculate_prepayment_impact(
        current_principal,
        current_rate,
        monthly_payment,
        net_prepayment,
        360
    )
    
    # Create metrics to show the impact
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Your One-Time Payment")
        st.metric("Extra Payment Amount", f"₹{prepayment_amount:,.2f}")
        st.metric("Bank's Fee", f"₹{prepayment_fee:,.2f}")
        st.metric("Actual Amount Applied to Loan", f"₹{net_prepayment:,.2f}")
        
    with col2:
        st.subheader("How This Helps You")
        st.metric("Interest You Would Save", f"₹{prepayment_impact['Interest Savings']:,.2f}")
        st.metric("Months Paid Off Early", f"{prepayment_impact['Months Saved']} months")
        
        # Calculate ROI on prepayment
        roi = (prepayment_impact['Interest Savings'] / prepayment_amount) * 100
        st.metric("Return on Your Money", f"{roi:.2f}%",
                 help="This is like an investment return - how much you get back for every rupee you put in")
        
        if roi > current_rate:
            st.success(f"✅ This is better than your loan interest rate of {current_rate:.2f}%")
        else:
            st.warning(f"⚠️ This is less than your loan interest rate of {current_rate:.2f}%")
    
    # Compare prepayment vs interest rate reduction
    st.subheader("Comparing All Your Options")
    st.markdown("Here's a side-by-side look at all three options:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("**Option 1: Keep Current Loan**")
        st.write(f"- Total Interest: ₹{current_total_interest:,.2f}")
        st.write(f"- Months Until Paid Off: {current_months}")
        st.write("- Cost: ₹0 (No action needed)")
        st.write("- Benefit: Keep your savings liquid")
    
    with col2:
        st.info("**Option 2: Lower Interest Rate**")
        st.write(f"- Total Interest: ₹{new_rate_total_interest:,.2f}")
        st.write(f"- Months Until Paid Off: {new_rate_months}")
        st.write(f"- Cost: ₹{rewriting_fee:,.2f} (One-time fee)")
        st.write(f"- Net Savings: ₹{net_savings:,.2f}")
    
    with col3:
        st.info("**Option 3: Make Extra Payment**")
        st.write(f"- Total Interest: ₹{prepayment_impact['New Total Interest']:,.2f}")
        st.write(f"- Months Until Paid Off: {current_months - prepayment_impact['Months Saved']}")
        st.write(f"- Cost: ₹{prepayment_amount:,.2f} (Your money) + ₹{prepayment_fee:,.2f} (Fee)")
        st.write(f"- Interest Savings: ₹{prepayment_impact['Interest Savings']:,.2f}")
    
    # Recommendation based on calculated scenarios
    st.subheader("Our Recommendation")
    
    if prepayment_impact['Interest Savings'] > net_savings and prepayment_impact['Interest Savings'] > 0:
        st.success("""
        ✅ **Best option: Make the extra payment**.
        
        You'll save more interest and pay off your loan faster compared to lowering your interest rate.
        """)
    elif net_savings > 0 and net_savings > prepayment_impact['Interest Savings']:
        st.success("""
        ✅ **Best option: Lower your interest rate**.
        
        The fee is worth it because you'll save more in the long run than with an extra payment.
        """)
    elif prepayment_amount > current_principal * 0.25:
        st.warning("""
        ⚠️ **Consider a smaller extra payment**.
        
        Your proposed payment is more than 25% of your remaining loan. You might want to keep some money for emergencies.
        """)
    else:
        st.error("""
        ❌ **Keep your current arrangement for now**.
        
        Neither option provides significant benefits. Consider saving more or looking for a better interest rate.
        """)
    
    # Explanation of the chart
    st.markdown("""
    ### How Extra Payment Affects Your Loan Balance
    This chart shows how your remaining loan balance will decrease over time, with and without the extra payment.
    Notice how the balance with the extra payment (blue line) is always lower and gets to zero faster.
    """)
    
    # Visualization of prepayment impact
    # Create a combined dataframe for the comparison
    df_orig = prepayment_impact['Original Schedule'][['Month', 'Balance']].copy()
    df_orig['Type'] = 'Without Extra Payment'
    
    df_new = prepayment_impact['New Schedule'][['Month', 'Balance']].copy()
    df_new['Type'] = 'With Extra Payment'
    
    df_combined = pd.concat([df_orig, df_new])
    
    fig = px.line(df_combined, x='Month', y='Balance', color='Type',
                 title='Loan Balance Over Time',
                 labels={'Month': 'Months from Now', 'Balance': 'Remaining Balance (₹)', 'Type': 'Payment Option'},
                 height=500,
                 color_discrete_map={'Without Extra Payment': '#FF9800', 'With Extra Payment': '#2196F3'})
    
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("Detailed Payment Schedule")
    st.markdown("""
    ### Your Complete Payment Schedule
    These tables show every payment you'll make until your loan is paid off.
    You can see how each payment is split between principal and interest.
    """)
    
    # Create tabs for different schedules
    amort_tab1, amort_tab2, amort_tab3 = st.tabs([
        "Current Loan Schedule",
        "Lower Interest Rate Schedule",
        "Extra Payment Schedule"
    ])
    
    with amort_tab1:
        st.subheader("Your Current Loan Schedule")
        # Format the DataFrame for display
        display_df = current_schedule.copy()
        display_df['Payment'] = display_df['Payment'].map('₹{:,.2f}'.format)
        display_df['Principal'] = display_df['Principal'].map('₹{:,.2f}'.format)
        display_df['Interest'] = display_df['Interest'].map('₹{:,.2f}'.format)
        display_df['Balance'] = display_df['Balance'].map('₹{:,.2f}'.format)
        display_df['Total Interest'] = display_df['Total Interest'].map('₹{:,.2f}'.format)
        
        st.dataframe(display_df, use_container_width=True)
        
        # Add explanation
        st.markdown("""
        **Understanding this table:**
        - **Month**: Which monthly payment this is
        - **Payment**: Your total monthly payment amount
        - **Principal**: How much of your payment reduces what you owe
        - **Interest**: How much goes to the bank as a fee
        - **Balance**: How much you still owe after this payment
        - **Total Interest**: How much interest you've paid so far
        """)
    
    with amort_tab2:
        st.subheader("Schedule with Lower Interest Rate")
        # Format the DataFrame for display
        display_df = new_rate_schedule.copy()
        display_df['Payment'] = display_df['Payment'].map('₹{:,.2f}'.format)
        display_df['Principal'] = display_df['Principal'].map('₹{:,.2f}'.format)
        display_df['Interest'] = display_df['Interest'].map('₹{:,.2f}'.format)
        display_df['Balance'] = display_df['Balance'].map('₹{:,.2f}'.format)
        display_df['Total Interest'] = display_df['Total Interest'].map('₹{:,.2f}'.format)
        
        st.dataframe(display_df, use_container_width=True)
    
    with amort_tab3:
        st.subheader("Schedule with Extra Payment")
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

# More user-friendly footer
st.markdown("""
## How to Use This Calculator:

1. **Enter your loan details** on the left side panel
   - Look at your loan statement for these numbers
   - Make sure to enter the correct interest rate and loan balance

2. **Check out each tab** at the top to see different options
   - The first tab shows your current loan situation
   - The second tab shows what happens if you get a lower interest rate
   - The third tab shows what happens if you make a one-time extra payment

3. **Look at our recommendation** to see which option saves you the most money

4. **Talk to your bank** before making any decisions

**Remember**: This calculator gives you estimates to help you decide. The actual numbers may vary slightly.

**Your Information is Private**: No data is collected or stored on any server.

Created with ❤️ using Streamlit
""")
