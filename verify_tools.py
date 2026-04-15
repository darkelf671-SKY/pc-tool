"""도구 자동 검증 - 배포 전 필수 실행

모든 도구가 BaseTool 계약을 준수하는지 자동 검증:
  1. Import 성공 여부
  2. tool_id / name 존재
  3. get_steps() 반환값 검증
  4. run() 메서드 구현 여부
  5. run() 내 log() 호출 step index가 get_steps()와 일치
  6. Dead code 감지 (도달 불가능한 return)
  7. symptom_map.json <-> requires_reboot 태그 일치

실행:
  python verify_tools.py          -> 전체 검증 (배포 전)
  python verify_tools.py --quick  -> 빠른 검증 (import + 구조만)
"""

import ast
import importlib
import json
import os
import sys
import textwrap

# 프로젝트 루트를 path에 추가
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class ToolVerifier:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.passed: list[str] = []

    def error(self, tool_id: str, msg: str):
        self.errors.append(f"[FAIL] {tool_id}: {msg}")

    def warn(self, tool_id: str, msg: str):
        self.warnings.append(f"[WARN] {tool_id}: {msg}")

    def ok(self, tool_id: str, msg: str):
        self.passed.append(f"[ OK ] {tool_id}: {msg}")

    # ── 1. Registry import + BaseTool 계약 ──

    def verify_registry(self) -> dict[str, object]:
        """TOOL_REGISTRY의 모든 도구를 import하고 인스턴스 생성"""
        try:
            from tools.registry import TOOL_REGISTRY
        except Exception as e:
            self.error("registry", f"tools/registry.py import 실패: {e}")
            return {}

        instances = {}
        for tool_id, cls in TOOL_REGISTRY.items():
            try:
                inst = cls()
                instances[tool_id] = inst

                # tool_id 일치
                if inst.tool_id != tool_id:
                    self.error(tool_id,
                               f"tool_id 불일치: 클래스={inst.tool_id}, 레지스트리={tool_id}")
                else:
                    self.ok(tool_id, "import + 인스턴스 생성 성공")

                # name 존재
                if not inst.name or not inst.name.strip():
                    self.error(tool_id, "name이 비어있음")

                # get_steps 반환값
                steps = inst.get_steps()
                if not isinstance(steps, list):
                    self.error(tool_id, f"get_steps()가 list를 반환하지 않음: {type(steps)}")
                elif len(steps) == 0:
                    self.error(tool_id, "get_steps()가 빈 리스트 반환  - 진행률 표시 불가")
                else:
                    self.ok(tool_id, f"get_steps() -> {len(steps)}단계")

            except Exception as e:
                self.error(tool_id, f"인스턴스 생성 실패: {e}")

        return instances

    # ── 2. AST 기반 run() 분석 ──

    def verify_run_method(self, tool_id: str, filepath: str, expected_steps: int):
        """run() 메서드의 AST를 분석하여 계약 준수 확인"""
        try:
            with open(filepath, encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=filepath)
        except SyntaxError as e:
            self.error(tool_id, f"구문 오류: {e}")
            return

        # 클래스 내 run 메서드 찾기
        run_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if item.name == "run":
                            run_node = item
                            break

        if run_node is None:
            self.error(tool_id, "run() 메서드를 찾을 수 없음")
            return

        # run() 본문 줄 수 (stub 감지)
        body_lines = run_node.end_lineno - run_node.lineno + 1
        if body_lines < 5:
            self.error(tool_id, f"run() 본문이 {body_lines}줄  - 껍데기(stub) 의심")
            return
        self.ok(tool_id, f"run() 본문 {body_lines}줄")

        # log() 호출에서 step index 수집
        step_indices = set()
        log_calls = 0
        for node in ast.walk(run_node):
            if isinstance(node, ast.Call):
                # log(message, step_index) 패턴
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name == "log" and len(node.args) >= 2:
                    log_calls += 1
                    idx_node = node.args[1]
                    if isinstance(idx_node, ast.Constant) and isinstance(idx_node.value, int):
                        if idx_node.value >= 0:
                            step_indices.add(idx_node.value)
                    elif isinstance(idx_node, ast.UnaryOp) and isinstance(idx_node.op, ast.USub):
                        pass  # -1 (정보 로그)
                    # 변수로 전달하는 경우는 정적 분석 한계

        if log_calls == 0:
            self.error(tool_id, "run()에서 log() 호출이 없음  - 진행률 표시 불가")
            return

        # step index 완전성 확인
        expected_set = set(range(expected_steps))
        missing = expected_set - step_indices
        extra = step_indices - expected_set

        if missing:
            self.error(tool_id,
                       f"누락된 step index: {sorted(missing)} "
                       f"(get_steps()={expected_steps}단계, 발견={sorted(step_indices)})")
        elif extra:
            self.warn(tool_id,
                      f"초과 step index: {sorted(extra)} "
                      f"(get_steps()={expected_steps}단계)")
        else:
            self.ok(tool_id, f"step index 0~{expected_steps-1} 모두 일치")

        # return 문 분석 (dead code 감지)
        self._check_dead_returns(tool_id, run_node, source)

    def _check_dead_returns(self, tool_id: str, func_node, source: str):
        """연속 return 문 감지 (dead code) - AST 부모 기반"""
        source_lines = source.splitlines()

        # AST 기반: 같은 블록(body) 내 연속 return만 감지
        for node in ast.walk(func_node):
            body = getattr(node, "body", None)
            if not isinstance(body, list):
                continue
            for i in range(len(body) - 1):
                stmt = body[i]
                next_stmt = body[i + 1]
                if isinstance(stmt, ast.Return) and isinstance(next_stmt, ast.Return):
                    self.error(tool_id,
                               f"Dead code: line {next_stmt.lineno}의 return은 "
                               f"line {stmt.lineno}의 return 뒤에 위치하여 도달 불가")

    # ── 3. 내부 헬퍼 메서드 분석 ──

    def verify_helper_methods(self, tool_id: str, filepath: str):
        """도구 파일의 헬퍼 메서드가 정상인지 확인"""
        try:
            with open(filepath, encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=filepath)
        except SyntaxError:
            return  # verify_run_method에서 이미 보고됨

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if item.name.startswith("_") and item.name != "run":
                            self._check_dead_returns(
                                f"{tool_id}.{item.name}", item, source)

    # ── 4. symptom_map ↔ requires_reboot 일치 검증 ──

    def verify_symptom_map(self, instances: dict[str, object]):
        """symptom_map.json의 태그가 도구의 requires_reboot과 일치하는지 확인"""
        map_path = os.path.join(ROOT, "data", "symptom_map.json")
        if not os.path.isfile(map_path):
            self.warn("symptom_map", "data/symptom_map.json 파일 없음  - 건너뜀")
            return

        with open(map_path, encoding="utf-8") as f:
            data = json.load(f)

        for cat in data.get("categories", []):
            for sym in cat.get("symptoms", []):
                tool_id = sym.get("tool_id", "")
                tags = sym.get("tags", [])
                sym_id = sym.get("id", "")

                if tool_id not in instances:
                    continue

                inst = instances[tool_id]
                has_reboot_tag = "reboot" in tags
                has_no_reboot_tag = "no_reboot" in tags

                if inst.requires_reboot and has_no_reboot_tag:
                    self.error(f"symptom:{sym_id}",
                               f"도구 {tool_id}는 requires_reboot=True인데 "
                               f"symptom '{sym_id}'에 'no_reboot' 태그 -> UI에서 재부팅 불필요로 표시됨")
                elif not inst.requires_reboot and has_reboot_tag:
                    self.warn(f"symptom:{sym_id}",
                              f"도구 {tool_id}는 requires_reboot=False인데 "
                              f"symptom '{sym_id}'에 'reboot' 태그")

        self.ok("symptom_map", "symptom_map ↔ requires_reboot 태그 검증 완료")

    # ── 5. 미사용 import 감지 ──

    def verify_unused_imports(self, tool_id: str, filepath: str):
        """간단한 미사용 import 감지"""
        try:
            with open(filepath, encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=filepath)
        except SyntaxError:
            return

        imports = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports.append((name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports.append((name, node.lineno))

        # 소스에서 사용 여부 확인 (import 줄 제외)
        source_lines = source.splitlines()
        for name, lineno in imports:
            if name == "*":
                continue
            # import 줄 자체를 제외한 나머지에서 이름 사용 여부
            used = False
            for i, line in enumerate(source_lines, 1):
                if i == lineno:
                    continue
                if name in line:
                    used = True
                    break
            if not used:
                self.warn(tool_id, f"미사용 import: '{name}' (line {lineno})")

    # ── 메인 실행 ──

    def run_all(self, quick: bool = False) -> bool:
        """전체 검증 실행. 성공 시 True."""
        print("=" * 60)
        print("  PC 문제해결 도우미  - 도구 자동 검증")
        print("=" * 60)
        print()

        # 1. Registry + 인스턴스
        print("[Phase 1] Registry import + BaseTool 계약 검증")
        instances = self.verify_registry()
        print(f"  -> {len(instances)}개 도구 로드 완료")
        print()

        if quick:
            return self._print_summary()

        # 2. AST 기반 run() 분석
        print("[Phase 2] run() 메서드 정적 분석 (step index, dead code)")
        tools_dir = os.path.join(ROOT, "tools")
        for tool_id, inst in instances.items():
            # 파일 경로 추정
            module = type(inst).__module__
            filepath = os.path.join(ROOT, module.replace(".", os.sep) + ".py")
            if not os.path.isfile(filepath):
                self.warn(tool_id, f"소스 파일을 찾을 수 없음: {filepath}")
                continue

            steps = inst.get_steps()
            self.verify_run_method(tool_id, filepath, len(steps))
            self.verify_helper_methods(tool_id, filepath)
            self.verify_unused_imports(tool_id, filepath)

        print()

        # 3. symptom_map 일치
        print("[Phase 3] symptom_map.json ↔ requires_reboot 태그 검증")
        self.verify_symptom_map(instances)
        print()

        return self._print_summary()

    def _print_summary(self) -> bool:
        print("=" * 60)
        print("  검증 결과")
        print("=" * 60)

        if self.passed:
            print(f"\n  PASS: {len(self.passed)}건")
            for msg in self.passed:
                print(f"    {msg}")

        if self.warnings:
            print(f"\n  WARN: {len(self.warnings)}건")
            for msg in self.warnings:
                print(f"    {msg}")

        if self.errors:
            print(f"\n  FAIL: {len(self.errors)}건")
            for msg in self.errors:
                print(f"    {msg}")

        print()
        if self.errors:
            print(f"  [X] 검증 실패  - {len(self.errors)}건의 오류를 수정하세요")
            print("      배포가 차단됩니다.")
            return False
        elif self.warnings:
            print(f"  [!] 검증 통과 (경고 {len(self.warnings)}건)")
            return True
        else:
            print("  [v] 검증 완전 통과")
            return True


def main():
    quick = "--quick" in sys.argv
    verifier = ToolVerifier()
    success = verifier.run_all(quick=quick)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
