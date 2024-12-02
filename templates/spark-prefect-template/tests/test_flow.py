from src.flows.flow import make_application_name_k8s_compatible


class TestMakeApplicationNameK8sCompatible:
    # Returns a valid Kubernetes-compatible name when all parameters are provided
    def test_valid_k8s_name_with_all_parameters(self):
        base_name = "my-application"
        app_name = "spark"
        name_to_hash = "unique-identifier"
        max_allowed_length = 63
        ui_postfix_len = 7
        hash_len = 6

        result = make_application_name_k8s_compatible(
            base_name,
            app_name,
            name_to_hash,
            max_allowed_length,
            ui_postfix_len,
            hash_len,
        )

        assert len(result) <= max_allowed_length
        assert result.startswith("my-application")
        assert "-spark" in result

    # Handles base names that are huge and exceed maximum allowed length
    def test_base_name_exact_max_length(self):
        base_name = "a" * 63
        app_name = None
        name_to_hash = "unique-identifier"
        max_allowed_length = 63
        ui_postfix_len = 7
        hash_len = 6

        result = make_application_name_k8s_compatible(
            base_name,
            app_name,
            name_to_hash,
            max_allowed_length,
            ui_postfix_len,
            hash_len,
        )

        assert len(result) <= max_allowed_length
        assert result.startswith("a" * (63 - ui_postfix_len - hash_len - 1))
