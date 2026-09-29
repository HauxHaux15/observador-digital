import os
import sys
import importlib
from pathlib import Path

# Configuração de caminhos do projeto
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
modules_path = BASE_DIR / "modules"
if modules_path.exists() and str(modules_path) not in sys.path:
    sys.path.append(str(modules_path))

# ------------------------------------------------------------
# CARREGAMENTO DINÂMICO DOS MÓDULOS
# ------------------------------------------------------------
BallCalibrator = None
try:
    mod = importlib.import_module("calibrator")
    BallCalibrator = getattr(mod, "BallCalibrator", None)
except Exception:
    try:
        mod = importlib.import_module("ball_calibrator")
        BallCalibrator = getattr(mod, "BallCalibrator", None)
    except Exception:
        pass

P0Adapter = None
try:
    mod = importlib.import_module("p0_adapter")
    P0Adapter = getattr(mod, "P0Adapter", None)
except Exception:
    pass

DeterministicPredictor = None
try:
    mod = importlib.import_module("deterministic_prediction")
    DeterministicPredictor = getattr(mod, "DeterministicPredictor", None)
except Exception:
    pass

calcular_rpm_rotor = None
try:
    mod = importlib.import_module("teste_rpm")
    calcular_rpm_rotor = getattr(mod, "calcular_rpm_rotor", None)
except Exception:
    pass


def main():
    print("=" * 60)
    print(" OBSERVADOR DIGITAL - ENGENHARIA REVERSA & FLUXO REVERSO")
    print("=" * 60)

    concurso = input("Digite o número do concurso (ex: 3783): ").strip()
    if not concurso:
        print("[ERRO] O número do concurso não foi informado.")
        sys.exit(1)

    video_path = BASE_DIR / "videos" / f"concurso_{concurso}.mp4"

    if not video_path.exists():
        print(f"[ERRO] Vídeo do concurso não encontrado: {video_path}")
        sys.exit(1)

    # ------------------------------------------------------------
    # ETAPA 1: CALIBRAÇÃO DAS 25 BOLINHAS NO TOPO (P0)
    # ------------------------------------------------------------
    print("\n[ETAPA 1] Abrindo calibrador para marcação do F0 (25 bolinhas)...")
    
    f0_selecionado = 0
    p0_matrix = None

    if BallCalibrator is not None:
        calibrador = BallCalibrator(video_path=str(video_path), concurso=concurso, frame_f0=0)
        calibrador.run()
        
        f0_selecionado = getattr(calibrador, 'locked_frame', getattr(calibrador, 'current_frame', 0))
        p0_matrix = getattr(calibrador, 'points', getattr(calibrador, 'p0_matrix', None))
    else:
        print("[AVISO] Módulo Calibrador não encontrado. Usando busca padrão.")

    print(f"[OK] Calibração de P0 concluída no Frame F0: {f0_selecionado}")

    # ------------------------------------------------------------
    # ETAPA 2: PROCESSAMENTO E RASTREAMENTO DAS 15 EXTRAÇÕES
    # ------------------------------------------------------------
    print("\n[ETAPA 2] Iniciando rastreamento das 15 extrações e geração do banco científico...")
    
    if P0Adapter is not None:
        adapter = P0Adapter(concurso=concurso, video_path=str(video_path), f0_frame=f0_selecionado, p0_data=p0_matrix)
        adapter.processar_video_completo()
    else:
        # Tenta disparar via LotterySessionManager caso o P0Adapter direto não esteja disponível
        try:
            mod_session = importlib.import_module("lottery_session_manager")
            SessionManager = getattr(mod_session, "LotterySessionManager", None)
            if SessionManager:
                session = SessionManager(str(video_path))
                session.run_from_f0(f0_frame=f0_selecionado, p0_data=p0_matrix)
        except Exception as e:
            print(f"[AVISO] Não foi possível rodar o rastreador automático: {e}")

    # ------------------------------------------------------------
    # ETAPA 3: SIMULAÇÃO FÍSICA NOMINAL E LIMPEZA DO TERMINAL
    # ------------------------------------------------------------
    report_path = BASE_DIR / "reports" / f"scientific_database_{concurso}.txt"

    if DeterministicPredictor is not None and report_path.exists():
        rpm_base = 114.28
        if callable(calcular_rpm_rotor):
            try:
                rpm_calculado = calcular_rpm_rotor(str(video_path), f0_selecionado)
                if 50 < rpm_calculado < 200:
                    rpm_base = rpm_calculado
            except Exception as e:
                print(f"[AVISO] Falha ao calcular RPM via teste_rpm: {e}")

        # Execução única sem o loop de varredura no terminal
        predictor = DeterministicPredictor(str(report_path))
        dezenas_previstas = predictor.predict_drawn_numbers(target_frames=1200, pas_rpm=rpm_base)
        print(f"⚡ [FÍSICA GÊMEO] Simulação Nominal no RPM Base ({rpm_base:.2f}): {dezenas_previstas}")

    print("\n" + "=" * 60)
    print("[PROCESSAMENTO CONCLUÍDO] Engenharia reversa finalizada.")


if __name__ == "__main__":
    main()