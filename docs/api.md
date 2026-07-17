# API Reference

## POST /search

Creates a search history record, queries all providers, stores comparison rows, and returns the full comparison.

## GET /history

Returns saved searches ordered by newest first.

## GET /comparison/{id}

Returns a search and all related comparison results.

## DELETE /history/{id}

Deletes the selected history item and cascades comparison results.
