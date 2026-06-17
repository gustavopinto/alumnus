"""
Popula o banco com professor gpinto@ufpa.br + 10 alunos fictícios.

Uso:
    docker compose exec backend python seed_local.py
"""
import json
import os
import urllib.request
from datetime import date, datetime, timedelta

from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://alumnus:alumnus123@db:5432/alumnus")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def fetch_bytes(url):
    try:
        with urllib.request.urlopen(url, timeout=6) as r:
            return r.read()
    except Exception:
        return None


def run():
    with Session() as db:
        from app.models import (
            Deadline, DeadlineInterest, FileUpload, GraphLayout,
            Institution, Milestone, Note, Professor, ProfessorGroup,
            ProfessorInstitution, Reading, Relationship, Reminder,
            Researcher, ResearchGroup, Tip, User,
        )

        # ── Instituição ────────────────────────────────────────────────────────
        inst = db.query(Institution).filter_by(domain="ufpa.br").first()
        if not inst:
            inst = Institution(name="UFPA", domain="ufpa.br")
            db.add(inst)
            db.flush()
        inst_id = inst.id

        # ── Professor ──────────────────────────────────────────────────────────
        prof_user = db.query(User).filter_by(email="gpinto@ufpa.br").first()
        if not prof_user:
            prof = Professor()
            db.add(prof)
            db.flush()

            db.add(ProfessorInstitution(
                professor_id=prof.id,
                institution_id=inst_id,
                institutional_email="gpinto@ufpa.br",
            ))

            group = ResearchGroup(
                name="Grupo de Engenharia de Software",
                institution_id=inst_id,
            )
            db.add(group)
            db.flush()

            db.add(ProfessorGroup(
                professor_id=prof.id,
                group_id=group.id,
                role_in_group="coordinator",
                institution_id=inst_id,
            ))

            prof_user = User(
                email="gpinto@ufpa.br",
                nome="Gustavo Pinto",
                password_hash=pwd_ctx.hash("12345"),
                role="professor",
                professor_id=prof.id,
                bio=(
                    "Professor do PPGCC-UFPA. Pesquisa em Engenharia de Software, "
                    "com foco em desempenho de software, análise estática e práticas "
                    "de desenvolvimento open source."
                ),
                lattes_url="http://lattes.cnpq.br/7000000000000001",
                scholar_url="https://scholar.google.com/citations?user=gpinto",
                github_url="https://github.com/gustavopinto",
                twitter_url="gustavopinto",
                interesses="Engenharia de Software, Desempenho, Análise Estática, OSS",
            )
            db.add(prof_user)
            db.flush()
        else:
            prof = db.query(Professor).get(prof_user.professor_id)
            group = db.query(ResearchGroup).filter_by(institution_id=inst_id).first()

        db.flush()
        prof_uid = prof_user.id
        prof_pid = prof.id
        group_id = group.id

        # ── 10 Alunos ──────────────────────────────────────────────────────────
        students = [
            dict(
                nome="Ana Beatriz Costa Silva", email="ana.beatriz@ufpa.br",
                status="mestrado", matricula="202201001",
                curso="Ciência da Computação", enrollment_date=date(2022, 3, 1),
                birth_date=date(1998, 4, 12),
                bio="Mestranda em Engenharia de Software. Pesquisa uso de LLMs para revisão automática de código.",
                interesses="LLMs para SE, Code Review, Análise Estática",
                lattes_url="http://lattes.cnpq.br/8800000000000001",
                scholar_url="https://scholar.google.com/citations?user=anabeatriz",
                github_url="https://github.com/anabeatrizcosta",
                linkedin_url="https://linkedin.com/in/ana-beatriz-costa",
                whatsapp="91991110001", avatar=15,
            ),
            dict(
                nome="Rafael Mendes Oliveira", email="rafael.mendes@ufpa.br",
                status="mestrado", matricula="202201002",
                curso="Ciência da Computação", enrollment_date=date(2022, 8, 1),
                birth_date=date(1997, 9, 23),
                bio="Mestrando pesquisando ferramentas de análise de código para IDEs.",
                interesses="IDEs, Code Analysis, Developer Tools",
                lattes_url="http://lattes.cnpq.br/8800000000000002",
                github_url="https://github.com/rafaelmendes",
                whatsapp="91991110002", avatar=52,
            ),
            dict(
                nome="Thiago Barbosa Rocha", email="thiago.barbosa@ufpa.br",
                status="doutorado", matricula="202001003",
                curso="Ciência da Computação", enrollment_date=date(2020, 3, 1),
                birth_date=date(1995, 2, 7),
                bio="Doutorando investigando predição de defeitos em pull requests com Machine Learning.",
                interesses="Machine Learning para SE, Pull Requests, Mineração de Repositórios",
                lattes_url="http://lattes.cnpq.br/8800000000000003",
                scholar_url="https://scholar.google.com/citations?user=thiagobarbosa",
                github_url="https://github.com/thiagobarbosa",
                linkedin_url="https://linkedin.com/in/thiago-barbosa-rocha",
                whatsapp="91991110003", avatar=33,
            ),
            dict(
                nome="Carlos Eduardo Souza", email="carlos.souza@ufpa.br",
                status="mestrado", matricula="202201004",
                curso="Sistemas de Informação", enrollment_date=date(2022, 3, 1),
                birth_date=date(1998, 11, 30),
                bio="Mestrando desenvolvendo ferramentas de visualização de evolução de software.",
                interesses="Visualização de Software, Evolução, Métricas de Código",
                github_url="https://github.com/carloseduardo",
                whatsapp="91991110004", avatar=65,
            ),
            dict(
                nome="Fernanda Castro Dias", email="fernanda.castro@ufpa.br",
                status="doutorado", matricula="201901005",
                curso="Ciência da Computação", enrollment_date=date(2019, 8, 1),
                birth_date=date(1993, 6, 18),
                bio="Doutoranda avaliando ferramentas de análise estática em projetos de larga escala.",
                interesses="Análise Estática, Qualidade de Software, Bugs de Segurança",
                lattes_url="http://lattes.cnpq.br/8800000000000005",
                scholar_url="https://scholar.google.com/citations?user=fernandacastro",
                github_url="https://github.com/fernandacastro",
                linkedin_url="https://linkedin.com/in/fernanda-castro-dias",
                whatsapp="91991110005", avatar=44,
            ),
            dict(
                nome="Júlia Nunes Alves", email="julia.nunes@ufpa.br",
                status="mestrado", matricula="202301006",
                curso="Ciência da Computação", enrollment_date=date(2023, 3, 1),
                birth_date=date(1999, 8, 5),
                bio="Mestranda pesquisando geração automática de documentação para APIs REST.",
                interesses="Documentação de APIs, Geração de Texto, NLP",
                github_url="https://github.com/julianunes",
                whatsapp="91991110006", avatar=39,
            ),
            dict(
                nome="Lucas Ferreira Gomes", email="lucas.ferreira@ufpa.br",
                status="doutorado", matricula="202001007",
                curso="Ciência da Computação", enrollment_date=date(2020, 8, 1),
                birth_date=date(1994, 12, 14),
                bio="Doutorando investigando anti-padrões de desempenho em aplicações mobile.",
                interesses="Desempenho Mobile, Anti-Padrões, Análise Dinâmica",
                lattes_url="http://lattes.cnpq.br/8800000000000007",
                scholar_url="https://scholar.google.com/citations?user=lucasferreira",
                github_url="https://github.com/lucasferreira",
                linkedin_url="https://linkedin.com/in/lucas-ferreira-gomes",
                whatsapp="91991110007", avatar=57,
            ),
            dict(
                nome="Letícia Moura Pereira", email="leticia.moura@ufpa.br",
                status="mestrado", matricula="202301008",
                curso="Engenharia da Computação", enrollment_date=date(2023, 3, 1),
                birth_date=date(2000, 3, 22),
                bio="Mestranda estudando práticas de contribuição em projetos de código aberto.",
                interesses="Open Source, Contribuição, Diversidade em TI",
                github_url="https://github.com/leticiamoura",
                linkedin_url="https://linkedin.com/in/leticia-moura-pereira",
                whatsapp="91991110008", avatar=21,
            ),
            dict(
                nome="Mariana Lima Santos", email="mariana.lima@ufpa.br",
                status="mestrado", matricula="202201009",
                curso="Ciência da Computação", enrollment_date=date(2022, 8, 1),
                birth_date=date(1997, 7, 9),
                bio="Mestranda pesquisando automação de code review em times ágeis.",
                interesses="Code Review, Agile, DevOps, Automação",
                lattes_url="http://lattes.cnpq.br/8800000000000009",
                github_url="https://github.com/marianalima",
                twitter_url="marianalima_se",
                whatsapp="91991110009", avatar=48,
            ),
            dict(
                nome="Pedro Alves Ribeiro", email="pedro.alves@ufpa.br",
                status="graduacao", matricula="201901010",
                curso="Ciência da Computação", enrollment_date=date(2019, 3, 1),
                birth_date=date(1999, 1, 15),
                bio="Graduando pesquisando métricas de refatoração e impactos na qualidade interna.",
                interesses="Refatoração, Débito Técnico, Métricas de Código",
                github_url="https://github.com/pedroalves",
                whatsapp="91991110010", avatar=62,
            ),
        ]

        researcher_ids = []
        user_ids = []

        for s in students:
            avatar_num = s.pop("avatar")
            existing = db.query(User).filter_by(email=s["email"]).first()
            if existing:
                researcher_ids.append(existing.researcher_id)
                user_ids.append(existing.id)
                continue

            researcher = Researcher(
                status=s["status"],
                group_id=group_id,
                orientador_id=prof_pid,
                matricula=s["matricula"],
                curso=s["curso"],
                enrollment_date=s["enrollment_date"],
            )
            db.add(researcher)
            db.flush()

            # Fotos via pravatar.cc (graceful fallback se não houver internet)
            photo_id = thumb_id = None
            photo_data = fetch_bytes(f"https://i.pravatar.cc/300?img={avatar_num}")
            if photo_data:
                f = FileUpload(data=photo_data, mime_type="image/jpeg",
                               original_name=f"avatar_{avatar_num}.jpg")
                db.add(f)
                db.flush()
                photo_id = f.id

                thumb_data = fetch_bytes(f"https://i.pravatar.cc/64?img={avatar_num}")
                if thumb_data:
                    t = FileUpload(data=thumb_data, mime_type="image/jpeg",
                                   original_name=f"avatar_{avatar_num}_thumb.jpg")
                    db.add(t)
                    db.flush()
                    thumb_id = t.id

            user = User(
                email=s["email"],
                nome=s["nome"],
                password_hash=pwd_ctx.hash("alumnus123"),
                role="researcher",
                researcher_id=researcher.id,
                bio=s.get("bio"),
                interesses=s.get("interesses"),
                lattes_url=s.get("lattes_url"),
                scholar_url=s.get("scholar_url"),
                github_url=s.get("github_url"),
                linkedin_url=s.get("linkedin_url"),
                twitter_url=s.get("twitter_url"),
                whatsapp=s.get("whatsapp"),
                birth_date=s.get("birth_date"),
                photo_file_id=photo_id,
                photo_thumb_file_id=thumb_id,
            )
            db.add(user)
            db.flush()

            researcher_ids.append(researcher.id)
            user_ids.append(user.id)
            print(f"  ✓ {s['nome']} ({'foto' if photo_id else 'sem foto'})")

        db.flush()

        # ── Milestones ────────────────────────────────────────────────────────
        for uid in user_ids:
            if not db.query(Milestone).filter_by(user_id=uid, type="entrada").first():
                db.add(Milestone(
                    user_id=uid, type="entrada", title="Entrada no Alumnus",
                    date=date.today() - timedelta(days=400),
                    description="Marco de ingresso no laboratório.",
                    created_by_id=prof_uid,
                ))

        qualifications = [
            (user_ids[2], date(2022, 5, 15), "Qualificação de Doutorado — Predição de defeitos em PRs"),
            (user_ids[4], date(2021, 9, 20), "Qualificação de Doutorado — Análise estática em larga escala"),
            (user_ids[6], date(2022, 3, 10), "Qualificação de Doutorado — Anti-padrões mobile"),
            (user_ids[0], date(2023, 6, 5),  "Qualificação de Mestrado — LLMs para revisão de código"),
            (user_ids[1], date(2023, 11, 8), "Qualificação de Mestrado — Análise de código em IDEs"),
            (user_ids[3], date(2023, 8, 22), "Qualificação de Mestrado — Visualização de evolução"),
        ]
        for uid, qdate, qtitle in qualifications:
            if not db.query(Milestone).filter_by(user_id=uid, type="qualificacao").first():
                db.add(Milestone(user_id=uid, type="qualificacao", title=qtitle,
                                 date=qdate, created_by_id=prof_uid))

        # ── Leituras ──────────────────────────────────────────────────────────
        readings = [
            (user_ids[0],
             "https://dl.acm.org/doi/10.1145/3524842.3528444",
             "An Empirical Study on Code Review Activity in Security-Sensitive Projects",
             "lido",
             "Revisores experientes detectam mais vulnerabilidades. Aponta necessidade de especialização."),
            (user_ids[0],
             "https://arxiv.org/abs/2302.07233",
             "Is ChatGPT a Good Code Reviewer?",
             "lendo", None),
            (user_ids[1],
             "https://dl.acm.org/doi/10.1145/3510003.3510204",
             "Neural Transfer Learning for Repairing Security Vulnerabilities in C Code",
             "lido", None),
            (user_ids[2],
             "https://arxiv.org/abs/2107.10714",
             "A Survey on Machine Learning Approaches for Code Clone Detection",
             "lendo", None),
            (user_ids[4],
             "https://dl.acm.org/doi/10.1145/3377811.3380370",
             "Revisiting the VCCFinder Approach for Identifying Security-Relevant Commits",
             "quero_ler", None),
            (user_ids[5],
             "https://arxiv.org/abs/2306.08987",
             "Automatic API Documentation Generation: a Systematic Review",
             "lido",
             "Survey abrangente. Boa referência para o capítulo 2 da dissertação."),
            (user_ids[6],
             "https://dl.acm.org/doi/10.1145/3468264.3468533",
             "An Empirical Study of Deep Learning Models for Mobile Code Smells",
             "lido", None),
            (user_ids[8],
             "https://arxiv.org/abs/2305.04722",
             "Automating Code Review Activities Using Large Language Models",
             "lendo", None),
        ]
        for uid, url, title, status, summary in readings:
            if not db.query(Reading).filter_by(user_id=uid, url=url).first():
                db.add(Reading(user_id=uid, url=url, title=title,
                               status=status, summary=summary, created_by_id=uid))

        # ── Notas do professor ────────────────────────────────────────────────
        notes = [
            (user_ids[0],
             "**Reunião 10/03/2024** — Ana apresentou resultados iniciais com GPT-4 para "
             "revisão automática. Acurácia de 78% na detecção de code smells. Próximo passo: "
             "comparar com CodeBERT e RoBERTa.\n\n**Pendente:** Expandir dataset para 300 projetos até 24/03."),
            (user_ids[0],
             "**Reunião 24/03/2024** — Comparativo finalizado. GPT-4 supera CodeBERT em 8 de 12 "
             "métricas. Dissertação em bom estado. Sugerido reforçar seção de ameaças à validade.\n\n"
             "**Meta:** Submeter para MSR 2025 até maio."),
            (user_ids[1],
             "**Reunião 15/02/2024** — Rafael demonstrou plugin para IntelliJ IDEA. "
             "Latência de 180ms para arquivos Java. Adicionar suporte a Python.\n\n"
             "**Ação:** Otimizar parser AST até 01/03."),
            (user_ids[1],
             "**Reunião 01/03/2024** — Latência caiu para 95ms após otimizações. "
             "Excelente progresso. Iniciar capítulo de implementação da dissertação."),
            (user_ids[2],
             "**Reunião 20/02/2024** — Thiago apresentou modelo XGBoost com F1 de 84% "
             "para predição de PRs problemáticos. Modelo falha em PRs com poucas linhas.\n\n"
             "**Próximo:** Coletar mais dados de PRs pequenos."),
            (user_ids[3],
             "**Reunião 05/03/2024** — Carlos mostrou protótipo de visualização. "
             "Interface intuitiva. Sugerido filtro temporal e exportação PNG.\n\n"
             "**User study** com 5 devs agendado para 19/03."),
            (user_ids[4],
             "**Reunião 12/02/2024** — Fernanda completou análise de 200 projetos com 5 "
             "ferramentas de análise estática. SonarQube tem recall de 92% mas precisão de 71%. "
             "SpotBugs é mais preciso para bugs de segurança.\n\n**Próximo:** Escrever artigo para SBES 2024."),
            (user_ids[5],
             "**Reunião 18/03/2024** — Júlia demonstrou gerador de documentação para 3 frameworks "
             "REST. Cobertura de 85% dos endpoints.\n\n**Meta:** Avaliação com 10 devs até 30/04."),
            (user_ids[6],
             "**Reunião 07/02/2024** — Lucas identificou 14 anti-padrões de desempenho mobile. "
             "Mais prevalentes: main thread blocking, sync I/O, memory leaks em activities.\n\n"
             "**Ação:** Implementar detector para os 5 mais frequentes."),
            (user_ids[8],
             "**Reunião 25/03/2024** — Mariana apresentou protocolo do estudo de caso com 3 times. "
             "Design bem estruturado.\n\n**Ação:** Submeter proposta ao comitê de ética até 15/04."),
        ]
        for uid, text in notes:
            db.add(Note(user_id=uid, text=text, created_by_id=prof_uid))

        # ── Lembretes ─────────────────────────────────────────────────────────
        today = date.today()
        reminders = [
            ("Revisar dissertação do Thiago Barbosa — cap. 4", today + timedelta(days=3), False),
            ("Enviar carta de recomendação para Ana Beatriz (bolsa sanduíche CAPES)", today + timedelta(days=7), False),
            ("Reunião com coordenação do PPGCC — vagas 2025", today + timedelta(days=12), False),
            ("Banca de qualificação do Lucas Ferreira — agendar membros", today + timedelta(days=15), False),
            ("Revisar proposta FAPESPA antes do envio", today + timedelta(days=18), False),
            ("Submeter relatório semestral CNPq", today + timedelta(days=21), False),
            ("SBES 2024 — confirmar presença (Curitiba, setembro)", today + timedelta(days=30), False),
            ("Ler artigo da Fernanda Castro — SBES", today - timedelta(days=1), True),
            ("Aprovar plano de trabalho do Pedro e da Letícia", today - timedelta(days=4), True),
        ]
        for text, due, done in reminders:
            if not db.query(Reminder).filter_by(text=text, created_by_id=prof_uid).first():
                db.add(Reminder(text=text, due_date=due, done=done,
                                created_by_id=prof_uid, institution_id=inst_id))

        # ── Manual (dicas) ────────────────────────────────────────────────────
        tips = [
            ("Como funciona o processo de qualificação no PPGCC-UFPA?",
             "A qualificação ocorre até o 18º mês para mestrado e 30º mês para doutorado. "
             "O aluno entrega uma proposta escrita e apresenta para uma banca de 3 membros. "
             "Em caso de reprovação, há segunda chance em 60 dias.\n\n"
             "**Documentos necessários:**\n- Proposta de pesquisa atualizada\n"
             "- Relatório de atividades\n- Comprovante de publicações\n\n"
             "Agende a banca com ao menos 30 dias de antecedência.", 1),
            ("Quais são as exigências de publicação para defesa?",
             "**Mestrado:** 1 artigo em veículo Qualis B2 ou superior.\n"
             "**Doutorado:** 2 artigos em Qualis A2 ou superior, ao menos 1 como primeiro autor.\n\n"
             "Os artigos devem ser relacionados ao tema da dissertação/tese. "
             "Verifique a tabela Qualis mais recente.\n\n"
             "**Dica:** Submeta cedo — revisão pode demorar 6–12 meses.", 2),
            ("Como acessar os servidores do laboratório remotamente?",
             "O laboratório usa VPN institucional (OpenVPN).\n\n"
             "1. Solicite acesso ao Prof. Gustavo\n"
             "2. Você receberá credenciais para a VPN\n"
             "3. Após conectar, acesse via SSH: `lab-server.ufpa.br`\n\n"
             "O cluster de GPUs requer agendamento prévio via planilha no WhatsApp do lab.", 3),
            ("Como funciona o pagamento das bolsas CAPES/CNPq?",
             "Bolsas são depositadas entre os dias 5 e 10 de cada mês no Banco do Brasil.\n\n"
             "Para manter a bolsa:\n- Registre atividades no SigaBolsas até dia 5\n"
             "- Não tenha vínculo empregatício > 20h/semana\n"
             "- Mantenha desempenho acadêmico satisfatório\n\n"
             "**Valores:** Mestrado CAPES: R$ 2.100/mês — Doutorado CAPES: R$ 3.100/mês", 1),
        ]
        for i, (q, a, pos) in enumerate(tips):
            if not db.query(Tip).filter_by(question=q).first():
                db.add(Tip(question=q, answer=a, position=pos,
                           author_id=prof_uid, institution_id=inst_id,
                           created_at=datetime.utcnow() - timedelta(days=30 - i)))

        # ── Prazos de conferências ─────────────────────────────────────────────
        deadlines_data = [
            ("MSR 2025 — Full Papers", "https://conf.researchr.org/home/msr-2025",
             date(2024, 11, 15), date(2024, 11, 8)),
            ("SBES 2024 — Trilha de Pesquisa", "https://cbsoft2024.ufmg.br/sbes.php",
             date(2024, 8, 5), date(2024, 7, 29)),
            ("ICSME 2024 — Research Track", "https://conf.researchr.org/home/icsme-2024",
             date(2024, 5, 17), date(2024, 5, 10)),
        ]
        deadline_ids = []
        for label, url, ddate, abstract_date in deadlines_data:
            d = db.query(Deadline).filter_by(label=label).first()
            if not d:
                d = Deadline(label=label, url=url, date=ddate, abstract_date=abstract_date,
                             institution_id=inst_id, created_by_id=prof_uid)
                db.add(d)
                db.flush()
            deadline_ids.append(d.id)

        for i, uid in enumerate(user_ids[:5]):
            did = deadline_ids[i % len(deadline_ids)]
            if not db.query(DeadlineInterest).filter_by(deadline_id=did, user_id=uid).first():
                db.add(DeadlineInterest(deadline_id=did, user_id=uid))

        # ── Relacionamentos entre pesquisadores ───────────────────────────────
        rel_pairs = [
            (researcher_ids[0], researcher_ids[1], "colaboracao"),
            (researcher_ids[0], researcher_ids[2], "co-autoria"),
            (researcher_ids[2], researcher_ids[6], "colaboracao"),
            (researcher_ids[4], researcher_ids[5], "colaboracao"),
            (researcher_ids[3], researcher_ids[7], "colaboracao"),
            (researcher_ids[8], researcher_ids[1], "co-autoria"),
        ]
        for src, tgt, rtype in rel_pairs:
            if src and tgt:
                if not db.query(Relationship).filter_by(
                    source_researcher_id=src, target_researcher_id=tgt
                ).first():
                    db.add(Relationship(source_researcher_id=src,
                                        target_researcher_id=tgt,
                                        relation_type=rtype))

        # ── Layout do grafo ───────────────────────────────────────────────────
        positions = [
            (220, 120), (620, 110), (760, 280), (330, 460), (120, 340),
            (580, 460), (700, 430), (90,  160), (200, 460), (450, 530),
        ]
        layout = {str(rid): {"x": x, "y": y}
                  for rid, (x, y) in zip(researcher_ids, positions) if rid}
        layout[f"p{prof_pid}"] = {"x": 450, "y": 280}
        existing = db.query(GraphLayout).filter_by(name="default").first()
        if existing:
            existing.layout_jsonb = layout
            existing.updated_at = datetime.utcnow()
        else:
            db.add(GraphLayout(name="default", layout_jsonb=layout))

        db.commit()

        from app.models import Researcher as R, User as U
        print("\n✓ Seed local concluído!")
        print(f"  Users:       {db.query(U).count()}")
        print(f"  Researchers: {db.query(R).count()}")
        print(f"  Notes:       {db.query(Note).count()}")
        print(f"  Reminders:   {db.query(Reminder).count()}")
        print(f"  Tips:        {db.query(Tip).count()}")


if __name__ == "__main__":
    run()
