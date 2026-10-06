# Restop — implementation of approved visual option 1

Goal: preserve the existing restaurant application, add a marketing landing, and carry the approved forest/peach/ivory visual system across the app.

Approved reference: first displayed ImageGen result, exec-39fdf5f6-afe6-4179-adde-9b2c1b123c03.png.

- [x] Inspect existing React/CRA application and live demo, maintain backend contract.
- [x] Public landing, functional demo entry, feature explanations, role tabs, FAQ, responsive navigation.
- [x] Shared typography and tokens, desktop sidebar, mobile drawer and bottom navigation, restyled login and all existing module shells.
- [x] Operational overview connected to current inventory and OCR documents, not marketing mock data.
- [x] Correct undefined report names, remove random sales amounts and fabricated date multipliers, test actual date filtering.
- [ ] Verify production build and desktop/mobile browser flows, correct visual regressions.
- [ ] Commit reviewable changes and deliver the verified result.

Constraints: preserve role restrictions, no backend/schema changes, no real customer data in marketing examples, no fabricated testimonials or savings claims. Maintain existing form handlers. Labels remain French. Visible focus, keyboard navigation, reduced-motion support.

Risks to verify: expired login, unavailable API, stock empty/loading/error states, date-only report fields, direct routes on reload, narrow screen overflow, controls obscured by navigation.
