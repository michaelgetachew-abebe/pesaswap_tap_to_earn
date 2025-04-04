from sqlalchemy.orm import Session
from models import Agent

def seed_data(db: Session):
    if not db.query(Agent).first():
        agents = [
            Agent(agentname="testagent", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="NatashaSokolova"),
            Agent(agentname="Yan01A1101", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="Emilianilson"),
            Agent(agentname="Yulia02B2111", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="Emilianilson"),
            Agent(agentname="Yuriy03C3121", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="Emilianilson"),
            Agent(agentname="Milena04D4131", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="Emilianilson", ),
            Agent(agentname="Nikolay05E5141", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="Emilianilson"),
            Agent(agentname="Aleksei01A1202", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="ValentinaSokolova"),
            Agent(agentname="Vadim02B2212", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="ValentinaSokolova"),
            Agent(agentname="Viktor03C3222", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="ValentinaSokolova"),
            Agent(agentname="Pasha04D4232", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="ValentinaSokolova"),
            Agent(agentname="Liza05E5242", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="ValentinaSokolova"),
            Agent(agentname="Zoya01A1303", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="TinaStewart"),
            Agent(agentname="Andrey02B2313", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="TinaStewart"),
            Agent(agentname="Anatoliy03C3323", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="TinaStewart"),
            Agent(agentname="Vitaliy04D4333", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="TinaStewart"),
            Agent(agentname="Danya05E5343", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="TinaStewart"),
            Agent(agentname="Valeria01A1404", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="LisaWilliams"),
            Agent(agentname="Vyacheslav02B2414", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="LisaWilliams"),
            Agent(agentname="Olga03C4424", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="LisaWilliams"),
            Agent(agentname="Vlad04D4434", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="LisaWilliams"),
            Agent(agentname="Karina05E5444", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="LisaWilliams"),
            Agent(agentname="Denis01A1505", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AshlynnReyes"),
            Agent(agentname="Vera02B2515", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AshlynnReyes"),
            Agent(agentname="Ekaterina03C4525", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AshlynnReyes"),
            Agent(agentname="Anna04D4535", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AshlynnReyes"),
            Agent(agentname="Temiloluwa05E5545", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AshlynnReyes"),
            Agent(agentname="Vadim01A1606", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AnnaVasilenko"),
            Agent(agentname="Aleksei02B2616", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AnnaVasilenko"),
            Agent(agentname="Aleksandr03C4626", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AnnaVasilenko"),
            Agent(agentname="Sasha04D4636", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AnnaVasilenko"),
            Agent(agentname="Vika05E5646", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AnnaVasilenko"),
            Agent(agentname="Stas01A1707", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AmeliaNixon"),
            Agent(agentname="Ira02B2717", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AmeliaNixon"),
            Agent(agentname="Dmitry03C3727", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AmeliaNixon"),
            Agent(agentname="Liliya04D4737", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AmeliaNixon"),
            Agent(agentname="Abigail05E5747", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AmeliaNixon"),
            Agent(agentname="Yaroslav01A1808", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="LenaLinderborg"),
            Agent(agentname="Snezhana02B2818", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="LenaLinderborg"),
            Agent(agentname="Maksim03C3828", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="LenaLinderborg"),
            Agent(agentname="Mark04D4838", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="LenaLinderborg"),
            Agent(agentname="Nsikanabasi05E5848", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="LenaLinderborg"),
            Agent(agentname="Aleksei01A1909", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AnastasiyaJohansson"),
            Agent(agentname="Tatyana02B2919", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AnastasiyaJohansson"),
            Agent(agentname="Nataliya03C3929", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AnastasiyaJohansson"),
            Agent(agentname="Viktoriya04D4939", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AnastasiyaJohansson"),
            Agent(agentname="David05E5949", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="AnastasiyaJohansson"),
            Agent(agentname="Liza01A1210", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="RosieRangel"),
            Agent(agentname="Valeria02B2320", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="RosieRangel"),
            Agent(agentname="Natasha03C3430", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="RosieRangel"),
            Agent(agentname="Ivanna04D4540", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="RosieRangel"),
            Agent(agentname="Nikita05E5650", password="$2b$12$LHtHlmPoMOZxwQ4w5.sweei9A7KDsmdHW5Oq2IC2Kedfn4lyhyUWW", persona="RosieRangel")]
        
        db.add_all(agents)
        db.commit()
        print("Database seeded with the default users")
    else:
        print("Database aleady seeded")