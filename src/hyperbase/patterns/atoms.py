def _matches_atomic_pattern(edge, atomic_pattern):
    ap_parts = atomic_pattern.parts()

    if len(ap_parts) == 0 or len(ap_parts[0]) == 0:
        return False

    # structural match
    struct_code = ap_parts[0][0]
    if struct_code == '.':
        if edge.not_atom:
            return False
    elif atomic_pattern.parens:
        if edge.atom:
            return False
    elif struct_code != '*' and not struct_code.isupper():
        if edge.not_atom:
            return False
        if edge.root() != atomic_pattern.root():
            return False

    # role match
    if len(ap_parts) > 1:
        pos = 1

        # type match
        ap_role = atomic_pattern.role()
        ap_type = ap_role[0]
        e_type = edge.type()
        n = len(ap_type)
        if len(e_type) < n or e_type[:n] != ap_type:
            return False

        e_atom = edge.inner_atom()

        if len(ap_role) > 1:
            e_role = e_atom.role()
            # check if edge role has enough parts to satisfy the wildcard
            # specification
            if len(e_role) < len(ap_role):
                return False

            # argroles match
            if ap_type[0] in {'B', 'P'}:
                ap_argroles_parts = ap_role[1].split('-')
                if len(ap_argroles_parts) == 1:
                    ap_argroles_parts.append('')
                ap_negroles = ap_argroles_parts[1]

                # fixed order?
                ap_argroles_posopt = ap_argroles_parts[0]
                e_argroles = e_role[1]
                if len(ap_argroles_posopt) > 0 and ap_argroles_posopt[0] == '{':
                    ap_argroles_posopt = ap_argroles_posopt[1:-1]
                else:
                    ap_argroles_posopt = ap_argroles_posopt.replace(',', '')
                    if len(e_argroles) > len(ap_argroles_posopt):
                        return False
                    else:
                        return ap_argroles_posopt.startswith(e_argroles)

                ap_argroles_parts = ap_argroles_posopt.split(',')
                ap_posroles = ap_argroles_parts[0]
                ap_argroles = set(ap_posroles) | set(ap_negroles)
                for argrole in ap_argroles:
                    min_count = ap_posroles.count(argrole)
                    # if there are argrole exclusions
                    fixed = ap_negroles.count(argrole) > 0
                    count = e_argroles.count(argrole)
                    if count < min_count:
                        return False
                    # deal with exclusions
                    if fixed and count > min_count:
                        return False
                pos = 2

            # match rest of role
            while pos < len(ap_role):
                if e_role[pos] != ap_role[pos]:
                    return False
                pos += 1

    # match rest of atom
    if len(ap_parts) > 2:
        e_parts = e_atom.parts()
        # check if edge role has enough parts to satisfy the wildcard
        # specification
        if len(e_parts) < len(ap_parts):
            return False

        while pos < len(ap_parts):
            if e_parts[pos] != ap_parts[pos]:
                return False
            pos += 1

    return True