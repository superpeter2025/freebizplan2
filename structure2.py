# --------------------------
# RUN
# --------------------------
if submitted:
    data = {
        "name": name,
        "email": email,
        "business_name": business_name,
        "idea": idea,
        "target_customer": target_customer,
        "problem": problem,
        "revenue": revenue,
        "competition": competition,
        "marketing": marketing,
        "budget": budget
    }

    with st.spinner("Generating business plans..."):
        try:
            plan_en = generate_plan(build_prompt_en(data))
            plan_fr = generate_plan(build_prompt_fr(data))

            pdf_en = create_pdf(plan_en)
            pdf_fr = create_pdf(plan_fr)

            # --------------------------
            # SEND EMAIL
            # --------------------------
            try:
                send_email(plan_en, plan_fr, pdf_en, pdf_fr, email)
                st.success("✅ Email sent successfully!")
            except Exception as e:
                st.error(f"❌ Email failed: {e}")

            # --------------------------
            # DISPLAY + DOWNLOAD
            # --------------------------
            st.subheader("Business Plan (English)")
            st.text_area("English Version", plan_en, height=300)

            st.download_button(
                "Download EN TXT",
                plan_en,
                file_name="business_plan_en.txt"
            )

            st.download_button(
                "Download EN PDF",
                pdf_en,
                file_name="business_plan_en.pdf"
            )

            st.subheader("Plan d'affaires (Français)")
            st.text_area("Version Française", plan_fr, height=300)

            st.download_button(
                "Télécharger TXT (FR)",
                plan_fr,
                file_name="business_plan_fr.txt"
            )

            st.download_button(
                "Télécharger PDF (FR)",
                pdf_fr,
                file_name="business_plan_fr.pdf"
            )

        except Exception as e:
            st.error(f"Error generating plan: {e}")
