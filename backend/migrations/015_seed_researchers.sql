-- Seed inicial de pesquisadores (professor orientador + 10 alunos)
-- Idempotente: ignora se já existir pelo e-mail

DO $$
DECLARE
    prof_id INTEGER;
BEGIN

    -- Professor orientador
    IF NOT EXISTS (SELECT 1 FROM researchers WHERE email = 'gustavo.pinto@ufpa.br') THEN
        INSERT INTO researchers (
            nome, status, email, ativo, registered,
            lattes_url, scholar_url, linkedin_url,
            interesses, observacoes,
            photo_url, created_at, updated_at
        ) VALUES (
            'Gustavo Pinto', 'professor', 'gustavo.pinto@ufpa.br', TRUE, TRUE,
            'http://lattes.cnpq.br/0000000000000001',
            'https://scholar.google.com/citations?user=gustavo',
            'https://linkedin.com/in/gustavopinto',
            'Engenharia de Software, Mining Software Repositories, Boas Práticas de Desenvolvimento',
            'Professor e orientador do grupo.',
            'https://i.pravatar.cc/300?img=3',
            now(), now()
        );
    END IF;

    SELECT id INTO prof_id FROM researchers WHERE email = 'gustavo.pinto@ufpa.br';

    -- 1. Doutoranda — IA / ML
    IF NOT EXISTS (SELECT 1 FROM researchers WHERE email = 'ana.beatriz@ufpa.br') THEN
        INSERT INTO researchers (
            nome, status, email, orientador_id, ativo, registered,
            matricula, curso, enrollment_date,
            lattes_url, scholar_url, linkedin_url, github_url, instagram_url,
            whatsapp, interesses, observacoes,
            photo_url, created_at, updated_at
        ) VALUES (
            'Ana Beatriz Ferreira', 'doutorado', 'ana.beatriz@ufpa.br', prof_id, TRUE, FALSE,
            '202101001', 'Ciência da Computação', '2021-03-01',
            'http://lattes.cnpq.br/0000000000000002',
            'https://scholar.google.com/citations?user=anabeatriz',
            'https://linkedin.com/in/anabeatrizferreira',
            'https://github.com/anabeatriz',
            'anabeatriz.pesquisa',
            '91991110001',
            'Aprendizado de Máquina, Redes Neurais, Processamento de Linguagem Natural',
            'Bolsista CNPq. Foco em modelos de linguagem para código-fonte.',
            'https://i.pravatar.cc/300?img=47',
            now(), now()
        );
    END IF;

    -- 2. Mestrando — Engenharia de Software
    IF NOT EXISTS (SELECT 1 FROM researchers WHERE email = 'carlos.souza@ufpa.br') THEN
        INSERT INTO researchers (
            nome, status, email, orientador_id, ativo, registered,
            matricula, curso, enrollment_date,
            lattes_url, linkedin_url, github_url, twitter_url,
            whatsapp, interesses, observacoes,
            photo_url, created_at, updated_at
        ) VALUES (
            'Carlos Eduardo Souza', 'mestrado', 'carlos.souza@ufpa.br', prof_id, TRUE, FALSE,
            '202201010', 'Engenharia de Software', '2022-03-01',
            'http://lattes.cnpq.br/0000000000000003',
            'https://linkedin.com/in/carloseduardosouza',
            'https://github.com/carloseduardo',
            '@carlos_sw',
            '91992220002',
            'Code Smells, Refatoração, Análise Estática',
            'Pesquisa sobre detecção automática de débito técnico.',
            'https://i.pravatar.cc/300?img=12',
            now(), now()
        );
    END IF;

    -- 3. Graduanda — Ciência de Dados
    IF NOT EXISTS (SELECT 1 FROM researchers WHERE email = 'mariana.lima@ufpa.br') THEN
        INSERT INTO researchers (
            nome, status, email, orientador_id, ativo, registered,
            matricula, curso, enrollment_date,
            lattes_url, github_url, instagram_url,
            whatsapp, interesses, observacoes,
            photo_url, created_at, updated_at
        ) VALUES (
            'Mariana Lima Costa', 'graduacao', 'mariana.lima@ufpa.br', prof_id, TRUE, FALSE,
            '202301020', 'Sistemas de Informação', '2023-03-01',
            'http://lattes.cnpq.br/0000000000000004',
            'https://github.com/marianalima',
            'mariana.lima.dev',
            '91993330003',
            'Visualização de Dados, Python, Análise Exploratória',
            'Iniciação científica. Trabalha com dados de repositórios open source.',
            'https://i.pravatar.cc/300?img=56',
            now(), now()
        );
    END IF;

    -- 4. Doutorando — Segurança
    IF NOT EXISTS (SELECT 1 FROM researchers WHERE email = 'rafael.mendes@ufpa.br') THEN
        INSERT INTO researchers (
            nome, status, email, orientador_id, ativo, registered,
            matricula, curso, enrollment_date,
            lattes_url, scholar_url, linkedin_url, github_url, twitter_url,
            whatsapp, interesses, observacoes,
            photo_url, created_at, updated_at
        ) VALUES (
            'Rafael Mendes Oliveira', 'doutorado', 'rafael.mendes@ufpa.br', prof_id, TRUE, FALSE,
            '202001002', 'Ciência da Computação', '2020-03-01',
            'http://lattes.cnpq.br/0000000000000005',
            'https://scholar.google.com/citations?user=rafaelmendes',
            'https://linkedin.com/in/rafaelmendesoliveira',
            'https://github.com/rafaelmendes',
            '@rafael_sec',
            '91994440004',
            'Segurança de Software, Vulnerabilidades, Análise de Malware, DevSecOps',
            'Tese sobre segurança em dependências de terceiros (supply chain).',
            'https://i.pravatar.cc/300?img=7',
            now(), now()
        );
    END IF;

    -- 5. Mestranda — IHC
    IF NOT EXISTS (SELECT 1 FROM researchers WHERE email = 'julia.nunes@ufpa.br') THEN
        INSERT INTO researchers (
            nome, status, email, orientador_id, ativo, registered,
            matricula, curso, enrollment_date,
            lattes_url, linkedin_url, instagram_url,
            whatsapp, interesses, observacoes,
            photo_url, created_at, updated_at
        ) VALUES (
            'Júlia Nunes Alves', 'mestrado', 'julia.nunes@ufpa.br', prof_id, TRUE, FALSE,
            '202302030', 'Engenharia de Software', '2023-03-01',
            'http://lattes.cnpq.br/0000000000000006',
            'https://linkedin.com/in/julianunnes',
            'julia.nunes.ux',
            '91995550005',
            'Interação Humano-Computador, UX Research, Acessibilidade, Design Inclusivo',
            'Pesquisa sobre acessibilidade em ferramentas de desenvolvimento.',
            'https://i.pravatar.cc/300?img=49',
            now(), now()
        );
    END IF;

    -- 6. Graduando — Desenvolvimento Mobile
    IF NOT EXISTS (SELECT 1 FROM researchers WHERE email = 'pedro.alves@ufpa.br') THEN
        INSERT INTO researchers (
            nome, status, email, orientador_id, ativo, registered,
            matricula, curso, enrollment_date,
            lattes_url, github_url, twitter_url,
            whatsapp, interesses, observacoes,
            photo_url, created_at, updated_at
        ) VALUES (
            'Pedro Henrique Alves', 'graduacao', 'pedro.alves@ufpa.br', prof_id, TRUE, FALSE,
            '202401040', 'Engenharia da Computação', '2024-03-01',
            'http://lattes.cnpq.br/0000000000000007',
            'https://github.com/pedroalves',
            '@pedroalves_dev',
            '91996660006',
            'Flutter, React Native, Android, iOS, Cross-platform',
            'IC focada em qualidade de apps mobile em projetos open source.',
            'https://i.pravatar.cc/300?img=15',
            now(), now()
        );
    END IF;

    -- 7. Doutorando — Sistemas Distribuídos
    IF NOT EXISTS (SELECT 1 FROM researchers WHERE email = 'thiago.barbosa@ufpa.br') THEN
        INSERT INTO researchers (
            nome, status, email, orientador_id, ativo, registered,
            matricula, curso, enrollment_date,
            lattes_url, scholar_url, linkedin_url, github_url,
            whatsapp, interesses, observacoes,
            photo_url, created_at, updated_at
        ) VALUES (
            'Thiago Barbosa Rocha', 'doutorado', 'thiago.barbosa@ufpa.br', prof_id, TRUE, FALSE,
            '201901003', 'Ciência da Computação', '2019-03-01',
            'http://lattes.cnpq.br/0000000000000008',
            'https://scholar.google.com/citations?user=thiagobarbosa',
            'https://linkedin.com/in/thiagobarbosarocha',
            'https://github.com/thiagobarbosa',
            '91997770007',
            'Microsserviços, Computação em Nuvem, Kubernetes, Observabilidade',
            'Em fase de escrita da tese. Publicou 3 artigos em conferências internacionais.',
            'https://i.pravatar.cc/300?img=21',
            now(), now()
        );
    END IF;

    -- 8. Mestranda — DevOps / Cloud
    IF NOT EXISTS (SELECT 1 FROM researchers WHERE email = 'fernanda.castro@ufpa.br') THEN
        INSERT INTO researchers (
            nome, status, email, orientador_id, ativo, registered,
            matricula, curso, enrollment_date,
            lattes_url, linkedin_url, github_url, twitter_url,
            whatsapp, interesses, observacoes,
            photo_url, created_at, updated_at
        ) VALUES (
            'Fernanda Castro Dias', 'mestrado', 'fernanda.castro@ufpa.br', prof_id, TRUE, FALSE,
            '202202050', 'Ciência da Computação', '2022-08-01',
            'http://lattes.cnpq.br/0000000000000009',
            'https://linkedin.com/in/fernandacastrodias',
            'https://github.com/fernandacastro',
            '@fernanda_devops',
            '91998880008',
            'CI/CD, Infrastructure as Code, Terraform, GitHub Actions',
            'Pesquisa práticas de DevOps em projetos open source brasileiros.',
            'https://i.pravatar.cc/300?img=44',
            now(), now()
        );
    END IF;

    -- 9. Graduanda — Jogos Digitais
    IF NOT EXISTS (SELECT 1 FROM researchers WHERE email = 'leticia.moura@ufpa.br') THEN
        INSERT INTO researchers (
            nome, status, email, orientador_id, ativo, registered,
            matricula, curso, enrollment_date,
            lattes_url, github_url, instagram_url,
            whatsapp, interesses, observacoes,
            photo_url, created_at, updated_at
        ) VALUES (
            'Letícia Moura Reis', 'graduacao', 'leticia.moura@ufpa.br', prof_id, TRUE, FALSE,
            '202401060', 'Análise e Desenvolvimento de Sistemas', '2024-03-01',
            'http://lattes.cnpq.br/0000000000000010',
            'https://github.com/leticiamoura',
            'leticia.games',
            '91999990009',
            'Game Development, Unity, Godot, Gamificação em Educação',
            'IC investigando uso de gamificação no ensino de programação.',
            'https://i.pravatar.cc/300?img=53',
            now(), now()
        );
    END IF;

    -- 10. Mestrando — Bioinformática
    IF NOT EXISTS (SELECT 1 FROM researchers WHERE email = 'lucas.ferreira@ufpa.br') THEN
        INSERT INTO researchers (
            nome, status, email, orientador_id, ativo, registered,
            matricula, curso, enrollment_date,
            lattes_url, scholar_url, linkedin_url, github_url,
            whatsapp, interesses, observacoes,
            photo_url, created_at, updated_at
        ) VALUES (
            'Lucas Ferreira Gomes', 'mestrado', 'lucas.ferreira@ufpa.br', prof_id, TRUE, FALSE,
            '202302070', 'Ciência da Computação', '2023-08-01',
            'http://lattes.cnpq.br/0000000000000011',
            'https://scholar.google.com/citations?user=lucasferreira',
            'https://linkedin.com/in/lucasferreiragomes',
            'https://github.com/lucasferreira',
            '91900010010',
            'Bioinformática, Análise de Sequências, Python, R',
            'Interdisciplinar com o dept. de Biologia. Analisa software científico.',
            'https://i.pravatar.cc/300?img=33',
            now(), now()
        );
    END IF;

    -- Layout em árvore: professor no topo, doutorandos > mestrandos > graduandos
    INSERT INTO graph_layouts (name, layout_jsonb, updated_at)
    SELECT 'default', jsonb_build_object(
        (SELECT id::text FROM researchers WHERE email = 'gustavo.pinto@ufpa.br'),   '{"x": 580,  "y": 50}'::jsonb,
        (SELECT id::text FROM researchers WHERE email = 'ana.beatriz@ufpa.br'),     '{"x": 300,  "y": 230}'::jsonb,
        (SELECT id::text FROM researchers WHERE email = 'rafael.mendes@ufpa.br'),   '{"x": 580,  "y": 230}'::jsonb,
        (SELECT id::text FROM researchers WHERE email = 'thiago.barbosa@ufpa.br'),  '{"x": 860,  "y": 230}'::jsonb,
        (SELECT id::text FROM researchers WHERE email = 'carlos.souza@ufpa.br'),    '{"x": 80,   "y": 410}'::jsonb,
        (SELECT id::text FROM researchers WHERE email = 'julia.nunes@ufpa.br'),     '{"x": 330,  "y": 410}'::jsonb,
        (SELECT id::text FROM researchers WHERE email = 'fernanda.castro@ufpa.br'), '{"x": 580,  "y": 410}'::jsonb,
        (SELECT id::text FROM researchers WHERE email = 'lucas.ferreira@ufpa.br'),  '{"x": 830,  "y": 410}'::jsonb,
        (SELECT id::text FROM researchers WHERE email = 'mariana.lima@ufpa.br'),    '{"x": 300,  "y": 590}'::jsonb,
        (SELECT id::text FROM researchers WHERE email = 'pedro.alves@ufpa.br'),     '{"x": 580,  "y": 590}'::jsonb,
        (SELECT id::text FROM researchers WHERE email = 'leticia.moura@ufpa.br'),   '{"x": 860,  "y": 590}'::jsonb
    ), now()
    WHERE NOT EXISTS (SELECT 1 FROM graph_layouts WHERE name = 'default');

    -- Relações de orientação (professor -> cada aluno)
    INSERT INTO relationships (source_researcher_id, target_researcher_id, relation_type)
    SELECT prof_id, r.id, 'orienta'
    FROM researchers r
    WHERE r.orientador_id = prof_id
      AND NOT EXISTS (
          SELECT 1 FROM relationships rel
          WHERE rel.source_researcher_id = prof_id
            AND rel.target_researcher_id = r.id
            AND rel.relation_type = 'orienta'
      );

END $$;
