# Equation Scanner & Solver (Web)

A zero-backend static web app that:

- Scans equations/variables using your device camera (Tesseract.js OCR)
- Renders live equation previews with KaTeX
- Evaluates expressions with mathjs, including helpers `integrate(fn, a, b)` and `sumN(fn, a, b)`
- Lets you define `I1(t)`, `I2(t)`, `I3(t)` and a main equation which can reference them

## Quick start

1. Serve the folder as static files (any static server works). Examples:

```bash
# Python
python3 -m http.server --directory /workspace 8080

# Node (if installed)
npx serve /workspace -l 8080 --single
```

2. Open `http://localhost:8080` in your browser.

## Usage

- Add variables at the top table (e.g., `alpha1`, `beta1`, `Q`, `R`, `theta`, `t1`, `mu`, `T`, `b`, `D0`).
- Enter expressions for `I1(t)`, `I2(t)`, `I3(t)` (they are functions of `t`).
- Enter the main equation. Example:

```
integrate(t -> I1(t) * exp(-R*t), theta, t1) +
integrate(t -> I2(t) * exp(-R*t), t1, mu) +
integrate(t -> I3(t) * exp(-R*t), mu, T)
```

- Click Evaluate to compute the numerical value.
- Click the camera icon next to any field to scan text via OCR. After capturing, click Recognize to insert text.

## Syntax notes

- Use `exp(x)` for e^x. Use `^` for powers. Standard mathjs operators apply.
- Lambdas: `t -> expressionInT`. Works inside `integrate` and `sumN`.
- Integrals: `integrate(fn, a, b)` performs numeric integration via adaptive Simpson.
- Sums: `sumN(fn, n0, n1)` performs an integer finite sum.
- The main equation can reference `I1(t)`, `I2(t)`, `I3(t)` directly.

## OCR quality tips

- Ensure good lighting and high contrast.
- Crop tightly; avoid borders; hold camera steady.
- You can edit the recognized text before evaluating.

## Optional: Mathpix

- This demo uses Tesseract.js only. You can add a toggle to call Mathpix's API if you have credentials and want better OCR for complex LaTeX. (Not included by default.)

## Limitations

- OCR may misread symbols; review text before evaluating.
- Numeric integration may be slow or imprecise for highly oscillatory/ill-conditioned functions.
- This is a client-only demo; do not use for high-stakes calculations without verification.

## Files

- `index.html` – UI and modal
- `style.css` – Styling
- `app.js` – Logic, OCR, math engine, evaluation

## License

MIT