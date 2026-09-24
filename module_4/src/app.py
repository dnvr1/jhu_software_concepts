"""Dynamic Flask analysis page backed by the SQLAlchemy Applicant model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import Flask, current_app, jsonify, render_template, request
from sqlalchemy.exc import SQLAlchemyError

from analysis_format import format_count, format_decimal, format_difference
import models
from orm_queries import run_complete_analysis
from scrape_refresh import scrape_manager


def prepare_analysis(results: dict[str, Any]) -> dict[str, Any]:
    """Convert ORM values to the assignment's display formats."""
    gpa, gre, gre_v, gre_aw = results["question_3"]
    original_count = int(results["question_8"])
    llm_count = int(results["question_9"])

    nationality_rows = [
        {
            "classification": classification,
            "count": format_count(applicant_count),
            "percentage": format_decimal(percentage, "%"),
        }
        for classification, applicant_count, percentage in results[
            "question_10"
        ]
    ]
    university_rows = [
        {
            "rank": rank,
            "university": university,
            "count": format_count(applicant_count),
            "percentage": format_decimal(percentage, "%"),
        }
        for rank, (university, applicant_count, percentage) in enumerate(
            results["question_11"], start=1
        )
    ]

    return {
        "database_rows": format_count(results["total_rows"]),
        "question_1": format_count(results["question_1"]),
        "question_2": format_decimal(results["question_2"], "%"),
        "question_3": {
            "gpa": format_decimal(gpa),
            "gre": format_decimal(gre),
            "gre_v": format_decimal(gre_v),
            "gre_aw": format_decimal(gre_aw),
        },
        "question_4": format_decimal(results["question_4"]),
        "question_5": format_decimal(results["question_5"], "%"),
        "question_6": format_decimal(results["question_6"]),
        "question_7": format_count(results["question_7"]),
        "question_8": format_count(original_count),
        "question_9": {
            "original": format_count(original_count),
            "llm": format_count(llm_count),
            "difference": format_difference(llm_count - original_count),
        },
        "question_10": nationality_rows,
        "question_11": university_rows,
        "generated_at": datetime.now().astimezone().strftime(
            "%B %d, %Y at %I:%M %p %Z"
        ),
    }


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Create a configurable Flask application without opening a connection.

    Tests can replace ``SESSION_FACTORY``, ``ANALYSIS_RUNNER``, and
    ``SCRAPE_MANAGER`` with deterministic doubles. Production uses the Module
    3 PostgreSQL and scraper implementations by default.
    """
    application = Flask(__name__)
    application.config.from_mapping(
        SESSION_FACTORY=models.SessionLocal,
        ANALYSIS_RUNNER=run_complete_analysis,
        SCRAPE_MANAGER=scrape_manager,
    )
    if test_config:
        application.config.update(test_config)

    @application.get("/")
    @application.get("/analysis")
    def analysis_page():
        manager = current_app.config["SCRAPE_MANAGER"]
        scrape_status = manager.snapshot()
        update_requested = request.args.get("updated") == "1"
        update_message = None
        if update_requested:
            if scrape_status["status"] == "running":
                update_message = (
                    "Analysis refreshed from the records currently in "
                    "PostgreSQL. New data is still being retrieved."
                )
            else:
                update_message = (
                    "Analysis updated using the latest records in PostgreSQL."
                )
        try:
            session_factory = current_app.config["SESSION_FACTORY"]
            analysis_runner = current_app.config["ANALYSIS_RUNNER"]
            with session_factory() as session:
                results = analysis_runner(session)
            analysis = prepare_analysis(results)
        except (RuntimeError, ValueError, SQLAlchemyError):
            current_app.logger.exception("Unable to load analysis results")
            return (
                render_template(
                    "analysis.html",
                    analysis=None,
                    scrape=scrape_status,
                    update_message=update_message,
                    error=(
                        "The analysis could not be loaded from PostgreSQL. "
                        "Confirm the database is running and try again."
                    ),
                ),
                503,
            )

        return render_template(
            "analysis.html",
            analysis=analysis,
            scrape=scrape_status,
            update_message=update_message,
            error=None,
        )

    @application.post("/pull-data")
    def pull_data():
        """Start one background pull, or reject the request while busy."""
        manager = current_app.config["SCRAPE_MANAGER"]
        started, status = manager.start()
        if not started:
            return jsonify(ok=False, busy=True, scrape=status), 409
        return jsonify(ok=True, busy=False, scrape=status), 202

    @application.post("/update-analysis")
    def update_analysis():
        """Refresh the analysis unless a pull is currently in progress."""
        manager = current_app.config["SCRAPE_MANAGER"]
        status = manager.snapshot()
        if status["status"] == "running":
            return jsonify(ok=False, busy=True, scrape=status), 409

        try:
            session_factory = current_app.config["SESSION_FACTORY"]
            analysis_runner = current_app.config["ANALYSIS_RUNNER"]
            with session_factory() as session:
                analysis = prepare_analysis(analysis_runner(session))
        except (RuntimeError, ValueError, SQLAlchemyError):
            current_app.logger.exception("Unable to update analysis results")
            return jsonify(ok=False, busy=False), 503
        return jsonify(ok=True, busy=False, analysis=analysis), 200

    @application.get("/scrape-status")
    def scrape_status():
        """Provide status updates without starting or interrupting a scrape."""
        manager = current_app.config["SCRAPE_MANAGER"]
        return jsonify(manager.snapshot())

    return application


app = create_app()
