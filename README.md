## Mid-term project CYBERPHYSICAL SYSTEMS AND I/O SECURITY
This is the GitHub page for the code for mid-term project replicating the result of the paper "Fingerprinting Electronic Control Units for Vehicle Intrusion Detection" (Figure 6/7 and 8). This GitHub page has been made by Jonas Ahlers Nielsen and Kasper Emil Hebsgaard. The file `simulation_fabr_sups.py` generates Figure 6/7, and the file `simulation_masquerade.py` generates Figure 8. The rest of the files can run the attacks and defences in separation. They need to run in separate terminals. They are not used for the report but are left there just in case of reference.

Generative AI (Google Gemini) has been used to assist us in writing this code.

### How to Run simulation with plots

To generate Figure 6/7, run the `simulation_fabr_sups.py` file.

To generate Figure 8, run the `simulation_masquerade.py` file.


### How to run first approach of individual files for attack "fabrication"

1. terminal: Run `cids.py`
2. terminal: Run `victim.py`
3. terminal: Run `attack_fabrication.py` and see the cids-terminal detect the attack.
