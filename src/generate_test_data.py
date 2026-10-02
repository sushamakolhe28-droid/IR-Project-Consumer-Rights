import json
import os

complaints = [
    # =========================================================================
    # ENGLISH (16 complaints: 8 dev, 8 test; 14 relevant, 2 unrelated)
    # =========================================================================
    {
        "id": "q1",
        "split": "dev",
        "lang": "en",
        "category": "Deficiency in Service",
        "text": "The airline refused to refund my ticket after cancellation.",
        "needs_human_verification": True,
        "qrels": {
            "CPA_s2_47_viii": 2,
            "CPA_s2_11": 2,
            "CPA_s39": 1
        }
    },
    {
        "id": "q2",
        "split": "dev",
        "lang": "en",
        "category": "Defective Goods",
        "text": "My local shop sold me a defective fridge, I want to file a complaint.",
        "needs_human_verification": True,
        "qrels": {
            "CPA_s2_10": 2,
            "CPA_s39": 2,
            "CPA_s2_6": 1
        }
    },
    {
        "id": "q3",
        "split": "dev",
        "lang": "en",
        "category": "Dark Pattern",
        "text": "Amazon is showing a different price at checkout than what was on the product page.",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_8": 2,
            "ECR_r5_3": 1,
            "DP_p5": 1
        }
    },
    {
        "id": "q4",
        "split": "dev",
        "lang": "en",
        "category": "Dark Pattern",
        "text": "A gym forced me to buy their shoes to use the membership.",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_4": 2,
            "DP_p5": 2,
            "CPA_s2_46": 1
        }
    },
    {
        "id": "q5",
        "split": "dev",
        "lang": "en",
        "category": "Dark Pattern",
        "text": "An online travel portal added travel insurance to my cart without my consent.",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_2": 2,
            "ECR_r4_9": 2,
            "DP_p5": 1
        }
    },
    {
        "id": "q6",
        "split": "dev",
        "lang": "en",
        "category": "Jurisdiction/Pecuniary",
        "text": "The seller claims my complaint is out of jurisdiction because the product is 60 lakhs.",
        "needs_human_verification": True,
        "qrels": {
            "JR_r4": 2,
            "CPA_s47": 1,
            "JR_r3": 1
        }
    },
    {
        "id": "q7",
        "split": "dev",
        "lang": "en",
        "category": "E-Commerce",
        "text": "I ordered a phone from an inventory ecommerce website but they refused to take it back.",
        "needs_human_verification": True,
        "qrels": {
            "ECR_r7_4": 2,
            "CPA_s2_47_viii": 2,
            "CPA_s39": 1
        }
    },
    {
        "id": "q8",
        "split": "test",
        "lang": "en",
        "category": "Misleading Ad",
        "text": "The misleading ad for weight loss was endorsed by a celebrity.",
        "needs_human_verification": True,
        "qrels": {
            "MAG_s14": 2,
            "MAG_s4": 2,
            "CPA_s2_28": 1,
            "CPA_s21": 1
        }
    },
    {
        "id": "q9",
        "split": "test",
        "lang": "en",
        "category": "Dark Pattern",
        "text": "I was tricked into an online subscription that I cannot cancel easily.",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_5": 2,
            "DP_p5": 2,
            "CPA_s2_47_viii": 1
        }
    },
    {
        "id": "q10",
        "split": "test",
        "lang": "en",
        "category": "Jurisdiction/Pecuniary",
        "text": "I was charged Rs 1.5 crore for an apartment and they delayed it, where to file?",
        "needs_human_verification": True,
        "qrels": {
            "JR_r4": 2,
            "CPA_s47": 1,
            "CPA_s2_11": 1
        }
    },
    {
        "id": "q11",
        "split": "test",
        "lang": "en",
        "category": "Dark Pattern",
        "text": "They are forcing me to sign up for a newsletter to buy the product on their store.",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_4": 2,
            "DP_p5": 1,
            "ECR_r4_9": 1
        }
    },
    {
        "id": "q12",
        "split": "test",
        "lang": "en",
        "category": "Dark Pattern",
        "text": "The e-commerce platform disguised a paid advertisement as an organic user review.",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_9": 2,
            "ECR_r6_3": 1,
            "MAG_s4": 1
        }
    },
    {
        "id": "q13",
        "split": "test",
        "lang": "en",
        "category": "Dark Pattern",
        "text": "The mobile app keeps nagging me with persistent popups to download their partner app.",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_10": 2,
            "DP_p5": 2,
            "CPA_s2_41": 1
        }
    },
    {
        "id": "q14",
        "split": "test",
        "lang": "en",
        "category": "Misleading Ad",
        "text": "I was lured with a cheap price but it was out of stock and they pushed a costly one.",
        "needs_human_verification": True,
        "qrels": {
            "MAG_s5": 2,
            "DP_annex_7": 2,
            "CPA_s2_47_i": 1
        }
    },
    {
        "id": "q15",
        "split": "dev",
        "lang": "en",
        "category": "Out-of-Scope",
        "text": "My neighbor physically assaulted me in the street and damaged my bicycle.",
        "needs_human_verification": True,
        "qrels": {}
    },
    {
        "id": "q16",
        "split": "test",
        "lang": "en",
        "category": "Out-of-Scope",
        "text": "The income tax department sent an audit notice demanding tax arrears for last year.",
        "needs_human_verification": True,
        "qrels": {}
    },

    # =========================================================================
    # HINGLISH (12 complaints: 6 dev, 6 test; 11 relevant, 1 unrelated)
    # =========================================================================
    {
        "id": "q17",
        "split": "dev",
        "lang": "hi-en",
        "category": "E-Commerce",
        "text": "Online marketplace mera refund nahi de raha bol raha hai force majeure hai.",
        "needs_human_verification": True,
        "qrels": {
            "ECR_r6_3": 2,
            "CPA_s2_47_viii": 2,
            "CPA_s39": 1
        }
    },
    {
        "id": "q18",
        "split": "dev",
        "lang": "hi-en",
        "category": "Dark Pattern",
        "text": "Bina bataye online cart me extra item daal diya basket sneaking karke.",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_2": 2,
            "ECR_r4_9": 2,
            "DP_p5": 1
        }
    },
    {
        "id": "q19",
        "split": "dev",
        "lang": "hi-en",
        "category": "Dark Pattern",
        "text": "Checkout ke time drip pricing laga ke payment page pe price badha diya.",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_8": 2,
            "DP_p5": 1,
            "ECR_r5_3": 1
        }
    },
    {
        "id": "q20",
        "split": "dev",
        "lang": "hi-en",
        "category": "Dark Pattern",
        "text": "Cancel karne ka option hi nahi mil raha subscription trap me phasa diya.",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_5": 2,
            "DP_p5": 2,
            "CPA_s2_47_viii": 1
        }
    },
    {
        "id": "q21",
        "split": "dev",
        "lang": "hi-en",
        "category": "Misleading Ad",
        "text": "Celebrity ne TV par jhootha ad kiya misleading advertisement ka claim nikla.",
        "needs_human_verification": True,
        "qrels": {
            "MAG_s14": 2,
            "MAG_s4": 2,
            "CPA_s2_28": 1,
            "CPA_s21": 1
        }
    },
    {
        "id": "q22",
        "split": "test",
        "lang": "hi-en",
        "category": "Procedure",
        "text": "Kya main electronic form se e-daakhil portal par complaint file kar sakta hu?",
        "needs_human_verification": True,
        "qrels": {
            "CPA_s35": 2,
            "CPA_s2_6": 1,
            "JR_r3": 1
        }
    },
    {
        "id": "q23",
        "split": "test",
        "lang": "hi-en",
        "category": "Jurisdiction/Pecuniary",
        "text": "Mera claim 3 crore ka hai commercial building delay par kahan file karu?",
        "needs_human_verification": True,
        "qrels": {
            "JR_r5": 2,
            "CPA_s58": 1,
            "CPA_s2_11": 1
        }
    },
    {
        "id": "q24",
        "split": "test",
        "lang": "hi-en",
        "category": "Dark Pattern",
        "text": "Forced action kar rahe hain app use karne ke liye newsletter subscribe karna compulsory kiya.",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_4": 2,
            "DP_p5": 2,
            "CPA_s2_46": 1
        }
    },
    {
        "id": "q25",
        "split": "test",
        "lang": "hi-en",
        "category": "Dark Pattern",
        "text": "Bait and switch kiya mere saath cheap price dikha ke out of stock bol diya.",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_7": 2,
            "MAG_s5": 2,
            "CPA_s2_47_i": 1
        }
    },
    {
        "id": "q26",
        "split": "test",
        "lang": "hi-en",
        "category": "Dark Pattern",
        "text": "SaaS software billing me bina consent ke credit card auto renew kar diya.",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_12": 2,
            "DP_annex_5": 1,
            "DP_p5": 1
        }
    },
    {
        "id": "q27",
        "split": "dev",
        "lang": "hi-en",
        "category": "Out-of-Scope",
        "text": "Traffic police ne red light jump karne ke liye 2000 ka online challan kaat diya.",
        "needs_human_verification": True,
        "qrels": {}
    },
    {
        "id": "q28",
        "split": "test",
        "lang": "hi-en",
        "category": "Dark Pattern",
        "text": "Confirm shaming kar rahe hain website par agar main paid plan opt out karu to shame feel karwate hain.",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_3": 2,
            "DP_p5": 2,
            "CPA_s2_41": 1
        }
    },

    # =========================================================================
    # HINDI (12 complaints: 6 dev, 6 test; 11 relevant, 1 unrelated)
    # =========================================================================
    {
        "id": "q29",
        "split": "dev",
        "lang": "hi",
        "category": "Jurisdiction/Pecuniary",
        "text": "मैंने एक करोड़ का फ्लैट खरीदा था जिसमें बिल्डर ने धोखा दिया, केस कहाँ दर्ज करूँ?",
        "needs_human_verification": True,
        "qrels": {
            "JR_r4": 2,
            "CPA_s47": 1,
            "CPA_s2_11": 1
        }
    },
    {
        "id": "q30",
        "split": "dev",
        "lang": "hi",
        "category": "Misleading Ad",
        "text": "टीवी पर उत्पाद का भ्रामक विज्ञापन देखकर सामान खरीदा, लेकिन वह पूरी तरह नकली और बेकार निकला।",
        "needs_human_verification": True,
        "qrels": {
            "MAG_s4": 2,
            "CPA_s2_28": 1,
            "CPA_s21": 1
        }
    },
    {
        "id": "q31",
        "split": "dev",
        "lang": "hi",
        "category": "E-Commerce",
        "text": "ई-कॉमर्स मार्केटप्लेस प्लेटफॉर्म ने खराब सामान की वापसी और पैसे लौटाने से मना कर दिया।",
        "needs_human_verification": True,
        "qrels": {
            "ECR_r6_3": 2,
            "CPA_s2_47_viii": 2,
            "CPA_s39": 1
        }
    },
    {
        "id": "q32",
        "split": "dev",
        "lang": "hi",
        "category": "Procedure",
        "text": "क्या उपभोक्ता इलेक्ट्रॉनिक रूप से जिला आयोग में शिकायत दर्ज करा सकता है?",
        "needs_human_verification": True,
        "qrels": {
            "CPA_s35": 2,
            "CPA_s2_6": 1,
            "JR_r3": 1
        }
    },
    {
        "id": "q33",
        "split": "dev",
        "lang": "hi",
        "category": "Dark Pattern",
        "text": "ऑनलाइन खरीदारी के चेकआउट पेज पर ड्रिप प्राइसिंग के तहत छुपे हुए शुल्क जोड़ दिए गए।",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_8": 2,
            "DP_p5": 1,
            "ECR_r5_3": 1
        }
    },
    {
        "id": "q34",
        "split": "test",
        "lang": "hi",
        "category": "Dark Pattern",
        "text": "ऑनलाइन टिकट बुक करते समय मेरी सहमति के बिना कार्ट में यात्रा बीमा जोड़ दिया गया।",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_2": 2,
            "ECR_r4_9": 2,
            "DP_p5": 1
        }
    },
    {
        "id": "q35",
        "split": "test",
        "lang": "hi",
        "category": "Dark Pattern",
        "text": "मेरा मासिक सब्सक्रिप्शन रद्द नहीं हो रहा है, ऐप ने कैंसिलेशन का बटन छुपा दिया है।",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_5": 2,
            "DP_p5": 2,
            "CPA_s2_47_viii": 1
        }
    },
    {
        "id": "q36",
        "split": "test",
        "lang": "hi",
        "category": "Dark Pattern",
        "text": "वेबसाइट पर सामान खरीदने के लिए मुझे अनावश्यक मोबाइल ऐप डाउनलोड करने पर मजबूर किया जा रहा है।",
        "needs_human_verification": True,
        "qrels": {
            "DP_annex_4": 2,
            "DP_p5": 2,
            "CPA_s2_46": 1
        }
    },
    {
        "id": "q37",
        "split": "test",
        "lang": "hi",
        "category": "Misleading Ad",
        "text": "क्या केंद्रीय उपभोक्ता संरक्षण प्राधिकरण भ्रामक विज्ञापन के लिए विज्ञापनदाता पर जुर्माना लगा सकता है?",
        "needs_human_verification": True,
        "qrels": {
            "CPA_s21": 2,
            "MAG_s4": 1,
            "CPA_s2_28": 1
        }
    },
    {
        "id": "q38",
        "split": "test",
        "lang": "hi",
        "category": "Procedure",
        "text": "उपभोक्ता आयोग में शिकायत दर्ज करने की समय सीमा क्या दो वर्ष है?",
        "needs_human_verification": True,
        "qrels": {
            "CPA_s69": 2,
            "CPA_s35": 1,
            "CPA_s2_6": 1
        }
    },
    {
        "id": "q39",
        "split": "dev",
        "lang": "hi",
        "category": "Jurisdiction/Pecuniary",
        "text": "राष्ट्रीय उपभोक्ता विवाद निवारण आयोग का अधिकार क्षेत्र और 2 करोड़ से अधिक का दावा।",
        "needs_human_verification": True,
        "qrels": {
            "JR_r5": 2,
            "CPA_s58": 1,
            "CPA_s39": 1
        }
    },
    {
        "id": "q40",
        "split": "test",
        "lang": "hi",
        "category": "Out-of-Scope",
        "text": "कंपनी ने मुझे बिना किसी पूर्व सूचना के नौकरी से निकाल दिया और मेरा तीन महीने का वेतन रोक लिया।",
        "needs_human_verification": True,
        "qrels": {}
    }
]

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    eval_dir = os.path.join(base_dir, 'data', 'evaluation')
    os.makedirs(eval_dir, exist_ok=True)
    
    out_path = os.path.join(eval_dir, 'complaints.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(complaints, f, indent=4, ensure_ascii=False)
        
    # Also save qrels in standard TREC format: query_id 0 doc_id grade
    qrels_path = os.path.join(eval_dir, 'qrels.trec')
    with open(qrels_path, 'w', encoding='utf-8') as f:
        for c in complaints:
            qid = c['id']
            for doc_id, grade in c['qrels'].items():
                f.write(f"{qid}\t0\t{doc_id}\t{grade}\n")
                
    print(f"Saved {len(complaints)} complaints to {out_path} and qrels to {qrels_path}")

if __name__ == "__main__":
    main()
