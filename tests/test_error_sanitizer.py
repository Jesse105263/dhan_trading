import unittest

from services.error_sanitizer import (
    classify_retryable,
    sanitize_error_message,
)


class ErrorSanitizerTest(
    unittest.TestCase
):
    def test_redacts_api_key(
        self,
    ) -> None:
        result = sanitize_error_message(
            "api_key=secret-key-value request failed"
        )

        self.assertNotIn(
            "secret-key-value",
            result,
        )
        self.assertIn(
            "[REDACTED]",
            result,
        )

    def test_redacts_access_token(
        self,
    ) -> None:
        result = sanitize_error_message(
            "access-token=super-secret"
        )

        self.assertNotIn(
            "super-secret",
            result,
        )
        self.assertIn(
            "[REDACTED]",
            result,
        )

    def test_redacts_password(
        self,
    ) -> None:
        result = sanitize_error_message(
            "password=my-password"
        )

        self.assertNotIn(
            "my-password",
            result,
        )

    def test_redacts_jwt(
        self,
    ) -> None:
        token = (
            "eyJabc."
            "eyJdef."
            "signature123"
        )

        result = sanitize_error_message(
            f"API failed: {token}"
        )

        self.assertNotIn(
            token,
            result,
        )

    def test_timeout_is_retryable(
        self,
    ) -> None:
        self.assertTrue(
            classify_retryable(
                TimeoutError(
                    "Timed out"
                )
            )
        )

    def test_validation_error_is_not_retryable(
        self,
    ) -> None:
        self.assertFalse(
            classify_retryable(
                ValueError(
                    "Invalid symbol"
                )
            )
        )


if __name__ == "__main__":
    unittest.main()
