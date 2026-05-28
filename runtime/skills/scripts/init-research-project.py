from __future__ import annotations



import argparse

from pathlib import Path



try:

    from .envctl.project_initializer import initialize_project

except ImportError:

    from envctl.project_initializer import initialize_project





def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument("--path", required=True)

    args = parser.parse_args()



    report = initialize_project(Path(args.path), update_trust=True)

    print("Research project initialized.")

    print(f"Project path: {report['project_path']}")

    print(f"Git repo: {report['git_repo']}")

    print(f"Project agents dir: {report['project_agents_dir']}")

    print(f"Dispatch dir: {report['dispatch_dir']}")

    print(f"Codex trust updated in: {report['codex_config_path']}")





if __name__ == "__main__":

    main()
