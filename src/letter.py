def generate_letter(extracted_info, predicted_frauds, raw_complaint):
    amount = extracted_info.get('amount')
    amount_str = f"Rs. {amount}" if amount else "[Amount]"
    
    platform = extracted_info.get('platforms', [])
    platform_str = ", ".join(platform) if platform else "[Opposite Party / Platform]"
    
    fraud_str = ", ".join(predicted_frauds) if predicted_frauds else "[Type of Fraud]"
    
    template = f"""
[Your Name]
[Your Address]
[Your Contact Information]

Date: [Current Date]

To,
The Grievance Officer / Manager,
{platform_str}

Subject: Formal Complaint regarding {fraud_str}

Dear Sir/Madam,

I am writing this letter to formally lodge a complaint regarding a recent transaction/experience with your platform/service. 

Details of the Complaint:
{raw_complaint}

Financial Implication: {amount_str}

This incident constitutes {fraud_str} and is a violation of my consumer rights as per the Consumer Protection Act, 2019. 

I request you to kindly resolve this matter immediately, issue a full refund of {amount_str}, and compensate for the mental agony caused. If I do not receive a favorable response within 15 days, I will be forced to file a formal complaint before the appropriate Consumer Disputes Redressal Commission and report this to the National Consumer Helpline (NCH).

Looking forward to your prompt response.

Yours sincerely,

[Your Name]
"""
    return template
