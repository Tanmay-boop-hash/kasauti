from voicetest.clients import synthesize, transcribe

SENTENCES = [
    "मेरा नंबर 9876543210 है",
    "मेरा नंबर नौ आठ सात छह पाँच चार तीन दो एक शून्य है",
    "पाँच लाख रुपये भेजना है",
    "₹5,00,000 भेजना है",
    "सुबह साढ़े नौ बजे मिलते हैं",
]

for s in SENTENCES:
    heard = transcribe(synthesize(s))
    print(f"SAID : {s}\nHEARD: {heard}\n")