# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Node.js tool that adds numbered-tone pinyin annotations to Chinese poetry (唐诗三百首). It reads a markdown source file, inserts a pinyin line above each Chinese text line, and writes the annotated result to a new file.

## Commands

- **Run the annotation tool:** `node add-pinyin.js`
  - Input: `docs/唐诗三百首.md`
  - Output: `docs/唐诗三百首_注音版.md`
- **Install dependencies:** `npm install`

## Architecture

Single-file application (`add-pinyin.js`) with no test framework or build step.

- **`add-pinyinToLine(line)`** — Converts a single line of text: each Chinese character gets its pinyin (numbered tone), each non-Chinese character is preserved as-is, all space-separated.
- **`addPinyinToText(text)`** — Splits text into lines, skips blank lines, and for each non-blank line outputs a pinyin annotation line followed by the original line.
- **`main()`** — Orchestrates file I/O: reads input, processes, writes output.

Uses `pinyin-pro` (v3.x) with `toneType: 'number'` (e.g., `han4` instead of `hàn`) for pinyin generation.

## Data Files

- `docs/唐诗三百首.md` — Source poetry collection (310 poems, 77 poets). Markdown structured with `##` for section headings, `###` for poem titles, `>` for poet attribution.
- `docs/唐诗三百首_注音版.md` — Generated output (do not hand-edit).
